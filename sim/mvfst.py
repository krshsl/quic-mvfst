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



from src.env import HANDSHAKE, MVFST_PKG, MVFST_PORT, RUN_SIM, SIM_FILE, RTT, are_files_identical
from tempfile import TemporaryDirectory, mkdtemp
from os import path, walk
from subprocess import run
from multiprocessing import Pool, cpu_count
from time import time

def rtt_mult(arg):
    '''
        this function handles running rtt across various threads
        :param arg: (iter, run_sim)
    '''
    temp_dir = mkdtemp(suffix="__"+str(arg[0]), dir=arg[1].rtt.name)
    rtt_mode = "true" if arg[1].rtt_mode else "false"
    sims = ','.join(["/%s"%SIM_FILE]*arg[1].rtt_iters)
    start = time()
    run([MVFST_PKG, '--mode=client', '--path=%s'%sims, '--outdir=%s'%temp_dir, '--early_data=%s'%rtt_mode, '--host=%s'%arg[1].host], capture_output=True)
    return time() - start

def check_mult(arg):
    '''
        this function handles verifying rtt file across various threads
        :param arg: (rtt dir, run_sim (class)) - use regex to get the index.html content
    '''
    not_work = []

    sim_file = path.join(arg[0], SIM_FILE)
    not_work.extend(are_files_identical(sim_file, arg[1]))
    files = [x for x in walk(arg[0], topdown=False)]
    files.pop()
    for file in files:
        not_work.extend(are_files_identical(file, arg[1]))

    return not_work

class CLIENT(RUN_SIM):
    def __init__(self, args):
        super().__init__(args)

    def handshake(self):
        '''
            this function checks for basic handshake
        '''
        status = True
        self.print_out("Running handshake...")
        self.hndshk = TemporaryDirectory(prefix=HANDSHAKE, dir=self.out_dir.name)
        start = time()
        run([MVFST_PKG, '--mode=client', '--path=/%s'%SIM_FILE, '--outdir=%s'%self.hndshk.name, '--host=%s'%self.host, '--early_data=true'], capture_output=True)
        f_time = time() - start
        out_file = path.join(self.hndshk.name, SIM_FILE)
        if len(are_files_identical(out_file, self)) == 0:
            self.print_out("handshake works...")
        else:
            self.debug_out(out_file, self.index)
            self.print_out("handshake doesn't work")
            status = False

        self.debug_out("handshake avg time: ", f_time)
        return f_time, status

    def multiple(self):
        '''
            this function loads the serve by sending files concurrently
        '''
        status = True
        self.print_out("Running rtt...")
        self.rtt = TemporaryDirectory(prefix=RTT, dir=self.out_dir.name)
        params = [(i, self) for i in range(self.rtt_iters)]
        with Pool(cpu_count()) as p:
            t_time = p.map(rtt_mult, params)
            f_time = sum(t_time)
            f_time /= self.rtt_iters**2

        self.print_out("Verifying rtt...")
        params = [(x[0], self) for x in walk(self.rtt.name, topdown=False)]
        params.pop()
        not_work = [self.rtt.name]*(len(params)-self.rtt_iters) if len(params) < self.rtt_iters else []
        with Pool(cpu_count()) as p:
            failures = p.map(check_mult, params)
            for fail in failures:
                if len(fail):
                    not_work.extend(fail)

        if len(not_work):
            self.debug_out('Rtt does not work for the following...')
            self.debug_out(not_work)
            self.print_out('Rtt not working file count : ', len(not_work))
            status = False
        else:
            self.print_out("Rtt seems to work fine for all files")

        self.print_out("Rtt avg time taken: ", f_time)
        self.debug_out(params[0])
        return f_time, status, len(not_work)


class SERVER(RUN_SIM):
    def __init__(self, args):
        super().__init__(args)

    def _start_server(self):
        # keep running the background or whatever...
        self.print_out(self.sim_url_dir)
        self.run_server([MVFST_PKG, '--mode=server', '-static_root=%s'%self.sim_url_dir, '--host=%s'%self.host], \
                MVFST_PORT)
