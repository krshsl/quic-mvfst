'''
    wget command - wget -p --save-headers https://www.example.org
    curl command - curl -D www.example.org/index.html -X GET www.example.org >> www.example.org/index.html
        Manually edit index.html and adjust the headers:
            Remove (if it exists): Transfer-Encoding: chunked
            Remove (if it exists): Alternate-Protocol: ...
            Add: X-Original-Url: https://www.example.org/

    client command - /vcpkg/packages/proxygen_x64-linux/tools/proxygen/hq --mode=client --host=127.0.0.1 --path=./index.html --early_data=true
    server command - /vcpkg/packages/proxygen_x64-linux/tools/proxygen/hq --mode=server --host=127.0.0.1 --static_root=/temp/www.example.org -early_data=true
'''



from src.env import HANDSHAKE, MVFST_PKG, MVFST_PORT, RUN_SIM, SIM_FILE, RTT_ITERS, RTT, are_files_identical
from tempfile import TemporaryDirectory, mkdtemp
from os import path, walk
from subprocess import run
from multiprocessing import Pool, cpu_count
from time import time

def rtt_mult(arg):
    '''
        this function handles running rtt across various threads
        :param arg: (rtt dir, iter, host addr, rtt_mode)
    '''
    temp_dir = mkdtemp(suffix="__"+str(arg[1]), dir=arg[0].name)
    avg = 0
    sims = ','.join(["/%s"%SIM_FILE]*RTT_ITERS)
    start = time()
    rtt_mode = "true" if arg[3] else "false"
    run([MVFST_PKG, '--mode=client', '--path=%s'%sims, '--outdir=%s'%temp_dir, '--early_data=%s'%rtt_mode, '--host=%s'%arg[2]], capture_output=True)
    avg += time()- start

    return avg

def check_mult(arg):
    '''
        this function handles verifying rtt file across various threads
        :param arg: (rtt dir, sim file content, debug_out (run_sim function)) - use regex to get the index.html content
    '''
    not_work = []

    sim_file = path.join(arg[0], SIM_FILE)
    not_work.extend(are_files_identical(sim_file, arg[1], arg[2]))

    for i in range(1, RTT_ITERS):
        curr_file = "%s_%d" % (sim_file, i)
        not_work.extend(are_files_identical(curr_file, arg[1], arg[2]))

    return not_work

class CLIENT(RUN_SIM):
    def __init__(self, host, rtt_mode, is_debug = False):
        super().__init__(host, is_debug)
        self.rtt_mode = rtt_mode

    def handshake(self):
        '''
            this function checks for basic handshake
        '''
        print("Running handshake...")
        self.hndshk = TemporaryDirectory(prefix=HANDSHAKE, dir=self.out_dir.name)
        out_file = path.join(self.hndshk.name, SIM_FILE)
        start = time()
        run([MVFST_PKG, '--mode=client', '--path=/%s'%SIM_FILE, '--outdir=%s'%self.hndshk.name, '--host=%s'%self.host, '--early_data=true'], capture_output=True)
        f_time = time() - start
        if len(are_files_identical(out_file, self.index, self.debug_out)) == 0:
            print("handshake works...")
        else:
            self.debug_out(out_file, self.index)
            print("handshake doesn't work")

        print("handshake avg time: ", f_time)

    def multiple(self):
        '''
            this function loads the serve by sending files concurrently
        '''
        print("Running rtt...")
        self.rtt = TemporaryDirectory(prefix=RTT, dir=self.out_dir.name)
        params = [(self.rtt, i, self.host, self.rtt_mode) for i in range(RTT_ITERS)]
        with Pool(cpu_count()) as p:
            t_time = p.map(rtt_mult, params)
            f_time = sum(t_time)
            f_time /= RTT_ITERS**2

        print("Verifying rtt...")
        params = [(x[0], self.index, self.debug_out) for x in walk(self.rtt.name, topdown=False)]
        params.pop()
        not_work = []
        with Pool(cpu_count()) as p:
            failures = p.map(check_mult, params)
            for fail in failures:
                if len(fail):
                    not_work.extend(fail)

        if len(not_work):
            # print('Rtt does not work for the following...')
            # print(not_work)
            print('Rtt not working file count : ', len(not_work))
        else:
            print("Rtt seems to work fine for all files")

        print("Rtt avg time taken: ", f_time)
        self.debug_out(params[0])


class SERVER(RUN_SIM):
    def __init__(self, host, pcap_file, is_debug = False):
        super().__init__(host, is_debug)
        self.pcap_file = pcap_file

    def start_server(self):
        # keep running the background or whatever...
        print(self.sim_url_dir)
        self.run_server([MVFST_PKG, '--mode=server', '-static_root=%s'%self.sim_url_dir, '--host=%s'%self.host], \
                MVFST_PORT, self.pcap_file)
