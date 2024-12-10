'''
    wget command - wget -p --save-headers https://www.example.org
        Manually edit index.html and adjust the headers:
            Remove (if it exists): Transfer-Encoding: chunked
            Remove (if it exists): Alternate-Protocol: ...
            Add: X-Original-Url: https://www.example.org/
    client command - ./out/Debug/epoll_quic_client --host=127.0.0.1 --disable_certificate_verification --num_requests=1 --port=6121 --body http://www.example.org --ignore_errors --one_connection_per_request --version_mismatch_ok > index.html
    server command - ./out/Debug/epoll_quic_server --certificate_file=net/tools/quic/certs/out/leaf_cert.pem --key_file=net/tools/quic/certs/out/leaf_cert.pkcs8 --allow_unknown_root_cert --quic_response_cache_dir=/tmp/quic-data/www.example.org/
'''



from src.env import HANDSHAKE, QUIC_CLIENT, QUIC_PORT, QUIC_SERVER, RUN_SIM, SIM_FILE, SIM_URL, RTT_ITERS, RTT, are_files_identical
from tempfile import TemporaryDirectory, mkdtemp
from src.parser import MyParser
from os import path, walk
from subprocess import run
from multiprocessing import Pool, cpu_count
from time import time

def rtt_mult(arg):
    '''
        this function handles running rtt across various threads
        :param arg: (rtt dir, iter, host addr)
    '''
    temp_dir = mkdtemp(suffix="__"+str(arg[1]), dir=arg[0].name)
    avg = 0
    for i in range(RTT_ITERS):
        temp_file = path.join(temp_dir, RTT+'_'+str(i))
        file = open(temp_file, "w") # num_requests can be increased if need be
        start = time()
        run([QUIC_CLIENT, '--disable_certificate_verification', '--num_requests=1', '--port=6121', \
            '--ignore_errors', '--one_connection_per_request', '--version_mismatch_ok', \
            '--host=%s'%arg[2], SIM_URL], stdout=file)
        avg += time()- start

    return avg

def check_mult(arg):
    '''
        this function handles verifying rtt file across various threads
        :param arg: (rtt dir, sim file)
    '''
    not_work = []
    sim_file = path.join(arg[0], SIM_FILE)

    for i in range(RTT_ITERS):
        curr_file = sim_file + '_' + str(i)
        if are_files_identical(curr_file, arg[1]):
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
        self.hndshk = TemporaryDirectory(prefix=HANDSHAKE, dir=self.out_dir.name)
        out_file = path.join(self.hndshk.name, HANDSHAKE)
        file = open(out_file, "w")
        start = time()
        run([QUIC_CLIENT, '--disable_certificate_verification', '--num_requests=1', '--port=6121', \
            '--ignore_errors', '--one_connection_per_request', '--version_mismatch_ok', \
            '--host=%s'%self.host, SIM_URL], stdout=file)
        f_time = time() - start

        if are_files_identical(out_file, self.sim_file):
            print("handshake works...")
        else:
            print("handshake doesn't work")

        print("handshake avg time: ", f_time)

    def multiple(self):
        '''
            this function loads the serve by sending files concurrently
        '''
        print("Running rtt...")
        self.rtt = TemporaryDirectory(prefix=RTT, dir=self.out_dir.name)
        params = [(self.rtt, i, self.host) for i in range(RTT_ITERS)]
        with Pool(cpu_count()) as p:
            t_time = p.map(rtt_mult, params)
            f_time = sum(t_time)
            f_time /= RTT_ITERS**2

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
            # print('Rtt does not work for the following...')
            # print(not_work)
            print('Rtt not working file count : ', len(not_work))
        else:
            print("Rtt seems to work fine for all files...")

        print("Rtt avg time: ", f_time)


class SERVER(RUN_SIM):
    def __init__(self, host, pcap_file):
        super().__init__(host)
        self.pcap_file = pcap_file

    def collect_data(self):
        # keep running the background or whatever...
        self.run_server([QUIC_SERVER, '--certificate_file=/chromium/src/net/tools/quic/certs/out/leaf_cert.pem', \
            '--key_file=/chromium/src/net/tools/quic/certs/out/leaf_cert.pkcs8', '--allow_unknown_root_cert', \
            '--quic_response_cache_dir=%s'%self.sim_url_dir], QUIC_PORT, self.pcap_file)

if __name__ == "__main__":
    parser = MyParser(description = "Run sim suite to collect data")
    parser.add_argument("--mode", choices=["server", "client"], type = str,
                        help = "Select the mode to run (server/client)", default="server")
    parser.add_argument("--host", type = str, help = "Input the server ip", required=True)
    parser.add_argument("--pcap_file", type = str, help = "Pcap File to save the server packet details.")
    args = parser.parse_args()
    if (args.mode == "client"):
        CLIENT(args.host).collect_data()
    else:
        if not (args.pcap_file):
                parser.error("Pcap_file missing")

        SERVER(args.host, args.pcap_file).collect_data()
