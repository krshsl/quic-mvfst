from tempfile import TemporaryDirectory
from os import path, mkdir
from subprocess import Popen, run
from signal import signal, SIGINT
from sys import exit
from re import findall, sub, DOTALL, IGNORECASE
from time import sleep


MVFST_PKG :str = "/vcpkg/packages/proxygen_x64-linux/tools/proxygen/hq"
QUIC_CLIENT :str = "/chromium/src/out/Debug/epoll_quic_client"
QUIC_SERVER :str = "/chromium/src/out/Debug/epoll_quic_server"
QUIC_OUT :str = "/chromium/src/out/index.html" # create a sample output ahead of time to compare easily
SIM_DIR :str = "quic"
SIM_FILE :str = "index.html" # ~ 1kb
SIM_URL :str = "www.example.org"
OUT_DIR :str = "out"
HANDSHAKE: str = "handshake"
RTT: str = "rtt"
RTT_ITERS: int = 256 # sends a square of this value, i.e., 128*128
INTERFACE: str = "eth0"
MVFST_PORT: int = 6666
QUIC_PORT: int = 6121

def get_html_content(src_file_path):
    with open(src_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    exclude_pattern = r"<script.*?>.*?</script>"
    html_pattern = r"<!DOCTYPE html>.*?</html>"
    cleaned_content = sub(exclude_pattern, '', content, flags=DOTALL | IGNORECASE)
    return findall(html_pattern, cleaned_content, flags=DOTALL | IGNORECASE)

# TODO : Move the common client and server code here??
def are_files_identical(src_file_path, index_content, debug_out, is_add_i = False):
    if not path.exists(src_file_path):
        if is_add_i:
            return [src_file_path]*RTT_ITERS
        else:
            return [src_file_path]


    not_working = []
    matches = get_html_content(src_file_path)

    for i, html in enumerate(matches):
        if index_content != html:
            debug_out("index_content", index_content)
            debug_out("new_html", html)
            not_working.append((src_file_path + "_" + str(i)) if is_add_i else src_file_path)

    if is_add_i and len(matches) != RTT_ITERS:
        return [src_file_path]*(len(matches)-RTT_ITERS)

    return not_working


class RUN_SIM:
    def __init__(self, host, is_debug = False):
        self.debug = is_debug
        self.host = host
        self.sleep_time = 60
        self.limit = 0
        self._create_root_folder()
        self._download_files()

    def _create_root_folder(self):
        self.sim_dir = TemporaryDirectory(prefix=SIM_DIR)
        self.out_dir = TemporaryDirectory(prefix=OUT_DIR, dir=self.sim_dir.name)

    def _download_files(self):
        temp_file = path.join(self.sim_dir.name, SIM_FILE)
        run(['wget', '-q', '-O', '%s'%temp_file, '--save-headers', '%s'%SIM_URL])

        mkdir(path.join(self.sim_dir.name, SIM_URL))
        self.sim_url_dir = path.join(self.sim_dir.name, SIM_URL)
        self.sim_file = path.join(self.sim_url_dir, SIM_FILE)
        with open(temp_file, 'r') as file:
            content = file.readlines()

        is_copied = False
        with open(self.sim_file, 'w') as file:
            for line in content:
                if not is_copied and ("Content-Length") in line.strip():
                    file.write('Content-Length: 1304\nX-Original-Url: https://%s/\n' % SIM_URL)
                    is_copied = True
                    continue

                file.write(line)

        matches = get_html_content(self.sim_file)
        for i, html in enumerate(matches):
            self.index = html
            break

    def run_server(self, run_args, port, pcap_file):
        processes = []

        def signal_handler(sig, frame):
            print("\nStopping processes...")
            for process in processes:
                process.terminate()
            exit(0)

        # Attach the signal handler for Ctrl+C
        signal(SIGINT, signal_handler)

        try:
            processes.append(Popen(run_args))
            processes.append(Popen(['tcpdump', '-i', 'eth0', 'udp', 'port %d' % port ,'-vv', '-X', '-Zroot', '-w%s' % pcap_file]))

            for process in processes:
                process.wait()
        except Exception as e:
            print(f"Error: {e}")
            for process in processes:
                process.terminate()
            exit(1)

    def debug_out(self, *args):
        if self.debug and self.limit < 5:
            print(args)
            self.limit += 1

    def handshake(self):
        raise NotImplementedError

    def multiple(self):
        raise NotImplementedError

    def collect_client_data(self):
        self.handshake()
        print("Running rtt by sending %d files" % RTT_ITERS**2)
        self.multiple()
        if self.debug:
            sleep(self.sleep_time)

    def start_server(self):
        raise NotImplementedError
