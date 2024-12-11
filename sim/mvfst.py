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



from src.env import HANDSHAKE, MVFST_PKG, MVFST_PORT, RUN_SIM, SIM_FILE, are_files_identical
from tempfile import TemporaryDirectory, mkdtemp
from os import path, walk
from subprocess import run
from time import time
from shutil import copy

def rtt_mult(arg):
    '''
        this function handles running rtt across various threads
        :param arg: (iter, run_sim)
    '''
    temp_dir = mkdtemp(suffix="__"+str(arg[0]), dir=arg[1].rtt.name)
    rtt_mode = "true" if arg[1].rtt_mode else "false"
    sims = ','.join(["/%s"%SIM_FILE]*arg[1].rtt_iters)
    start = time()
    run([arg[1].client_file, '--mode=client', '--path=%s'%sims, '--outdir=%s'%temp_dir, '--early_data=%s'%rtt_mode, '--host=%s'%arg[1].host], capture_output=True)
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
        filename = path.basename(MVFST_PKG)
        self.client_file = path.join(self.sim_dir.name, filename)
        copy(MVFST_PKG, self.client_file)

    def handshake(self):
        '''
            this function checks for basic handshake
        '''
        status = True
        self.print_out("Running handshake...")
        self.hndshk = TemporaryDirectory(prefix=HANDSHAKE, dir=self.out_dir.name)
        start = time()
        run([self.client_file, '--mode=client', '--path=/%s'%SIM_FILE, '--outdir=%s'%self.hndshk.name, '--host=%s'%self.host, '--early_data=true'], capture_output=True)
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
        return self._multiple(rtt_mult, check_mult)


class SERVER(RUN_SIM):
    def __init__(self, args):
        super().__init__(args)
        filename = path.basename(MVFST_PKG)
        self.server_file = path.join(self.sim_dir.name, filename)
        copy(MVFST_PKG, self.server_file)

    def _start_server(self):
        # keep running the background or whatever...
        self.print_out(self.sim_url_dir)
        self.run_server([MVFST_PKG, '--mode=server', '-static_root=%s'%self.sim_url_dir, '--host=%s'%self.host], \
                MVFST_PORT)
