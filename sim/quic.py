'''
    wget command - wget -p --save-headers https://www.example.org
    curl command - curl -D www.example.org/index.html -X GET www.example.org >> www.example.org/index.html
        Manually edit index.html and adjust the headers:
            Remove (if it exists): Transfer-Encoding: chunked
            Remove (if it exists): Alternate-Protocol: ...
            Add: X-Original-Url: https://www.example.org/

    client command - ./out/Debug/epoll_quic_client --host=127.0.0.1 --disable_certificate_verification --num_requests=1 --port=6121 --one_connection_per_request --version_mismatch_ok http://www.example.org > index.html
    server command - ./out/Debug/epoll_quic_server --certificate_file=net/tools/quic/certs/out/leaf_cert.pem --key_file=net/tools/quic/certs/out/leaf_cert.pkcs8 --allow_unknown_root_cert --quic_response_cache_dir=/tmp/quic-data/www.example.org/
'''



from src.env import HANDSHAKE, QUIC_CLIENT, QUIC_PORT, QUIC_SERVER, RUN_SIM, SIM_FILE, RTT, are_files_identical
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
    temp_file = path.join(temp_dir, SIM_FILE)
    file = open(temp_file, "w") # num_requests can be increased if need be
    run_args = [QUIC_CLIENT, '--disable_certificate_verification', '--num_requests=%d'%arg[1].rtt_iters, '--port=6121', \
        '--one_connection_per_request', '--version_mismatch_ok', '--host=%s'%arg[1].host, arg[1].sim_url]
    if not arg[1].rtt_mode:
        run_args.remove('--one_connection_per_request')

    start = time()
    run(run_args, stdout=file)
    return time() - start

def check_mult(arg):
    '''
        this function handles verifying rtt file across various threads
        :param arg: (rtt dir, run_sim (class)) - use regex to get the index.html content
    '''
    sim_file = path.join(arg[0], SIM_FILE)
    return are_files_identical(sim_file, arg[1], True)

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
        out_file = path.join(self.hndshk.name, SIM_FILE)
        file = open(out_file, "w")
        start = time()
        run([QUIC_CLIENT, '--disable_certificate_verification', '--num_requests=1', '--port=6121', \
            '--ignore_errors', '--one_connection_per_request', '--version_mismatch_ok', \
            '--host=%s'%self.host, self.sim_url], stdout=file)
        f_time = time() - start

        if len(are_files_identical(out_file, self)) == 0:
            self.print_out("handshake works...")
        else:
            # self.debug_out(out_file, self.index)
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
            self.print_out("Rtt seems to work fine for all files...")

        self.print_out("Rtt avg time taken: ", f_time)
        self.debug_out(params[0])
        return f_time, status, len(not_work)


class SERVER(RUN_SIM):
    def __init__(self, args):
        super().__init__(args)

    def _start_server(self):
        # keep running the background or whatever...
        self.run_server([QUIC_SERVER, '--certificate_file=/chromium/src/net/tools/quic/certs/out/leaf_cert.pem', \
            '--key_file=/chromium/src/net/tools/quic/certs/out/leaf_cert.pkcs8', '--allow_unknown_root_cert', \
            '--quic_response_cache_dir=%s'%self.sim_url_dir], QUIC_PORT, self.pcap_file)
