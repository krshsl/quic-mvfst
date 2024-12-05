from src.env import HANDSHAKE, MVFST_PKG, RUN_SIM, SIM_FILE, RTT_ITERS, RTT
from tempfile import TemporaryDirectory, mkdtemp
from src.parser import MyParser
from os import path, walk
from subprocess import run
from filecmp import cmp
from multiprocessing import Pool, cpu_count

def rtt_mult(arg):
    '''
        this function handles running rtt across various threads
        :param arg: (rtt dir, iter, host addr)
    '''
    temp_dir = mkdtemp(suffix="__"+str(arg[1]), dir=arg[0].name)
    sims = ','.join(["/%s"%SIM_FILE]*RTT_ITERS)
    run([MVFST_PKG, '--mode=client', '--path=%s'%sims, '--outdir=%s'%temp_dir, '--host=%s'%arg[2]], capture_output=True)

def check_mult(arg):
    '''
        this function handles verifying rtt file across various threads
        :param arg: (rtt dir, sim file)
    '''
    not_work = []

    sim_file = path.join(arg[0], SIM_FILE)
    if not path.exists(sim_file) or not cmp(sim_file, arg[1]):
        not_work.append(sim_file)

    for i in range(1, RTT_ITERS):
        curr_file = sim_file + '_' + str(i)
        if not path.exists(curr_file) or not cmp(curr_file, arg[1]):
            not_work.append(curr_file)

    return not_work

class CLIENT(RUN_SIM):
    def __init__(self, host):
        super().__init__(host)

    def collect_data(self):
        self.handshake()
        self.multiple()

    def handshake(self):
        '''
            this function checks for basic handshake
        '''
        print("Running handshake...")
        self.hndshk = TemporaryDirectory(suffix=HANDSHAKE, dir=self.out_dir.name)
        out_file = path.join(self.hndshk.name, SIM_FILE)
        run([MVFST_PKG, '--mode=client', '--path=/%s'%SIM_FILE, '--outdir=%s'%self.hndshk.name, '--host=%s'%self.host], capture_output=True)
        if cmp(out_file, self.sim_file):
            print("handshake works...")
        else:
            print("handshake doesn't work")

    def multiple(self):
        '''
            this function loads the serve by sending files concurrently
        '''
        print("Running rtt...")
        self.rtt = TemporaryDirectory(suffix=RTT, dir=self.out_dir.name)
        params = [(self.rtt, 0, self.host) for i in range(RTT_ITERS)]
        with Pool(cpu_count()) as p:
            p.map(rtt_mult, params)

        print("Verifying rtt...")
        params = [(x[0], self.sim_file) for x in walk(self.rtt.name, topdown=False)]
        params.pop()
        not_work = []
        with Pool(cpu_count()) as p:
            failures = p.map(check_mult, params)
            for fail in failures:
                if len(fail):
                    not_work.extend(fail)

        if len(not_work):
            print(not_work)
        else:
            print("Rtt seems to work fine...")


class SERVER(RUN_SIM):
    def __init__(self, host):
        super().__init__(host)

    def collect_data(self):
        # keep running the background or whatever...
        run([MVFST_PKG, '--mode=server', '-static_root=%s'%self.sim_dir.name, '--host=%s'%self.host])

if __name__ == "__main__":
    parser = MyParser(description = "Run sim suite to collect data")
    parser.add_argument("--mode", choices=["server", "client"], type = str,
                        help = "Select the mode to run (server/client)", default="server")
    parser.add_argument("--host", type = str, help = "Input the server ip", required=True)
    args = parser.parse_args()
    if (args.mode == "client"):
        CLIENT(args.host).collect_data()
    else:
        SERVER(args.host).collect_data()
