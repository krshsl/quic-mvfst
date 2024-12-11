from src.utils import H_Test, R_Test
from tempfile import TemporaryDirectory
from subprocess import Popen, CalledProcessError, run, PIPE
from re import findall, DOTALL, IGNORECASE
from multiprocessing import Pool, cpu_count
from signal import signal, SIGINT
from os import path, sep, walk
from time import sleep
from sys import exit


MVFST_PKG :str = "/vcpkg/packages/proxygen_x64-linux/tools/proxygen/hq"
QUIC_FLDR :str = "/chromium/src/out/Debug"
QUIC_CLIENT :str = "/chromium/src/out/Debug/epoll_quic_client"
QUIC_SERVER :str = "/chromium/src/out/Debug/epoll_quic_server"
QUIC_OUT :str = "/chromium/src/out/index.html" # create a sample output ahead of time to compare easily
SIM_DIR :str = "mvfst_quic"
SIM_FILE :str = "index.html"
SIM_URL :str = "www.example.org"
THROUGHPUT_URL: str = "demo.borland.com"
OUT_DIR :str = "out"
HANDSHAKE: str = "handshake"
RTT: str = "rtt"
THROUGHPUT: str = "throughput"
RTT_ITERS: int = 128 # sends a square of this value, i.e., 128*128
INTERFACE: str = "eth0"
MVFST_PORT: int = 6666
QUIC_PORT: int = 6121
CREATE_COPY: bool = False

def get_html_content(src_file_path):
    with open(src_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    html_pattern = r"<!DOCTYPE html>.*?</html>"
    '''exclude not needed since we're comparnig the same file???'''
    # from re import findall, sub, DOTALL, IGNORECASE
    # exclude_pattern = r"<script.*?>.*?</script>"
    # cleaned_content = sub(exclude_pattern, '', content, flags=DOTALL | IGNORECASE)
    # return findall(html_pattern, cleaned_content, flags=DOTALL | IGNORECASE)
    return findall(html_pattern, content, flags=DOTALL | IGNORECASE)

# TODO : Move the common client and server code here??
def are_files_identical(src_file_path, run_sim, is_add_i = False):
    if not path.exists(src_file_path):
        if is_add_i:
            return [src_file_path]*run_sim.rtt_iters
        else:
            return [src_file_path]


    not_working = []
    matches = get_html_content(src_file_path)
    for i, html in enumerate(matches):
        if run_sim.index != html:
            run_sim.debug_out("index_content", run_sim.index)
            run_sim.debug_out("new_html", html)
            not_working.append((src_file_path + "_" + str(i)) if is_add_i else src_file_path)

    if is_add_i and len(matches) != run_sim.rtt_iters:
        return [src_file_path]*(len(matches)-run_sim.rtt_iters)

    return not_working


class RUN_SIM:
    def __init__(self, args):
        self.log_level = args.log
        self.host = args.host
        self.sleep_time = 60
        self.test_throughput = args.throughput
        self.no_dump = args.no_dump

        if args.log:
            self.rtt_iters = 2
        else:
            self.rtt_iters = RTT_ITERS//2 if self.test_throughput else RTT_ITERS

        # self.rtt_mode = args.rtt_mode
        self.rtt_mode = 1 # defaulting to 1 atm
        self.pcap_file = args.pcap_file
        self.server_file = None
        self.client_file = None
        self._create_root_folder()
        self._set_sim_files()

    def _create_root_folder(self):
        self.sim_dir = TemporaryDirectory(prefix=SIM_DIR)
        self.out_dir = TemporaryDirectory(prefix=OUT_DIR, dir=self.sim_dir.name)

    def _set_sim_files(self):
        self.sim_url = THROUGHPUT_URL if self.test_throughput else SIM_URL
        self.sim_url_dir = path.abspath(path.join(sep, "sim", self.sim_url))
        self.sim_file = path.join(self.sim_url_dir, SIM_FILE)
        if not path.exists(self.sim_file):
            print(self.sim_file)
            raise FileNotFoundError

        matches = get_html_content(self.sim_file)
        for i, html in enumerate(matches):
            self.index = html
            break

    def signal_handler(self, sig, frame):
        print("\nStopping processes...")
        self.processes[0].terminate()
        self.processes[1].terminate()
        if not self.pcap_file:
            stdout, stderr = self.processes[1].communicate()
            print(stdout, stderr)
        exit(0)

    def run_server(self, run_args, port):
        self.processes = []

        # Attach the signal handler for Ctrl+C
        signal(SIGINT, self.signal_handler)

        try:
            self.processes.append(Popen(run_args))
            if not self.no_dump:
                if self.pcap_file:
                    print(self.pcap_file)
                    self.processes.append(Popen(['tcpdump', '-i', 'eth0', 'udp', 'port %d' % port ,'-vv', '-X', '-Zroot', '-w%s' % self.pcap_file]))
                else: # comment this out if you don't want tcp dump
                    self.processes.append(Popen(['tcpdump', '-i', 'eth0', 'udp', 'port %d' % port ,'-vv', '-X', '-Zroot'], stdout=PIPE, stderr=PIPE, text=True)) # proceed without appending result

            for process in self.processes:
                process.wait()
        except Exception as e:
            print(f"Error: {e}")
            for process in self.processes:
                process.terminate()
            exit(1)

    def print_out(self, *args):
        if self.log_level >= 1:
            print(args)

    def debug_out(self, *args):
        if self.log_level == 2:
            print(args)

    def handshake(self) -> H_Test:
        raise NotImplementedError

    def multiple(self) -> R_Test:
        raise NotImplementedError

    def _multiple(self, rtt_mult, check_mult) -> R_Test:
        '''
            this function loads the serve by sending files concurrently
        '''
        status = True
        self.print_out("Running rtt...")
        self.rtt = TemporaryDirectory(prefix=RTT, dir=self.out_dir.name)
        params = [(i, self) for i in range(self.rtt_iters)]
        with Pool(cpu_count()) as p:
            time_list = p.map(rtt_mult, params)
            avg_time = sum(time_list)

        self.print_out("Verifying rtt...")
        params = [(x[0], self) for x in walk(self.rtt.name, topdown=False)]
        params.pop()
        fail_list = [self.rtt.name]*(len(params)-self.rtt_iters) if len(params) < self.rtt_iters else []
        with Pool(cpu_count()) as p:
            failures = p.map(check_mult, params)
            for fail in failures:
                if len(fail):
                    fail_list.extend(fail)

        if len(fail_list):
            self.debug_out('Rtt does not work for the following...')
            self.debug_out(fail_list)
            self.print_out('Rtt not working file count : ', len(fail_list))
            status = False
        else:
            self.print_out("Rtt seems to work fine for all files")

        avg_time /= ((self.rtt_iters**2)-len(fail_list))
        self.print_out("Rtt avg time taken: ", avg_time)
        self.debug_out(params[0])
        return R_Test(avg_time, status, time_list, len(fail_list), self.rtt_iters)

    def _start_server(self):
        raise NotImplementedError

    def _wait(self):
        command = ['ping', self.host, '-c', '1']
        try:
            run(command, check=True, stdout=PIPE, stderr=PIPE)
            return False
        except CalledProcessError:
            return True

    def collect_client_data(self, instance):
        if not self.client_file:
            raise NotImplementedError

        max_tries = 20 # wait for server to start...
        while self._wait() and max_tries:
            sleep(5)
            max_tries -= 1

        if max_tries == 0:
            print("Unable to ping destination")
            exit(1)

        h_test = self.handshake()
        r_test = self.multiple()

        # show data in end to regex easily!!
        print("Throughput Mode") if self.test_throughput else print("Normal Mode")
        h_test.show_data(instance, self.sim_url, (path.getsize(self.sim_file)/1024))
        r_test.show_data(instance, self.sim_url, (path.getsize(self.sim_file)/1024))
        if self.log_level >= 2:
            sleep(self.sleep_time)

    def start_server(self):
        if not self.server_file:
            raise NotImplementedError

        print("Throughput Mode") if self.test_throughput else print("Normal Mode")
        self._start_server()
