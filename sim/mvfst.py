from src.env import HANDSHAKE, MVFST_PKG, RUN_SIM, SIM_FILE, RTT_ITERS, RTT
from src.parser import MyParser
from os import path
from subprocess import run
from filecmp import cmp

class CLIENT(RUN_SIM):
    def __init__(self, host):
        super().__init__(host)

    def collect_data(self):
        self.handshake()
        self.multiple()

    def handshake(self):
        print("Running handshake...")
        self.hndshk = path.join(self.out_dir, HANDSHAKE)
        self._rm_mk_dir(self.hndshk)
        out_file = path.join(self.hndshk, SIM_FILE)
        run([MVFST_PKG, '--mode=client', '--path=/%s'%SIM_FILE, '--outdir=%s'%self.hndshk, '--host=%s'%self.host])
        if not cmp(out_file, self.sim_file):
            print("doesn't work")
        else:
            print("works...")

    def multiple(self):
        print("Running rtt...")
        self.rtt = path.join(self.out_dir, RTT)
        self._rm_mk_dir(self.rtt)
        out_file = path.join(self.rtt, SIM_FILE)
        sims = ','.join(["/"+SIM_FILE]*RTT_ITERS)
        run([MVFST_PKG, '--mode=client', '--path=%s'%sims, '--outdir=%s'%self.rtt, '--host=%s'%self.host])
        if not cmp(out_file, self.sim_file):
            print("doesn't work")
        else:
            print("works...")

class SERVER(RUN_SIM):
    def __init__(self, host):
        super().__init__(host)

    def collect_data(self):
        # keep running the background or whatever...
        run([MVFST_PKG, '--mode=server', '-static_root=%s'%self.sim_dir, '--host=%s'%self.host])

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
