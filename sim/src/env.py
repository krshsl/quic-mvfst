from tempfile import TemporaryDirectory
from os import path, mkdir
from subprocess import Popen, run
from signal import signal, SIGINT
from sys import exit


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
RTT_ITERS: int = 128 # sends a square of this value, i.e., 128*128
INTERFACE: str = "eth0"
MVFST_PORT: int = 6666
QUIC_PORT: int = 6121

# TODO : Use the beautify to test maybe??
# TODO : Move the common client and server code here??
def are_files_identical(out_file, src_file): # brute force approach to compare files, but it does the trick!
    return path.exists(out_file) and (path.getsize(src_file)-100 < path.getsize(out_file) < path.getsize(src_file)+500)


class RUN_SIM:
    def __init__(self, host):
        self.host = host
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
                    file.write('Content-Length: 1304\nX-Original-Url: https://www.example.org/\n')
                    is_copied = True
                    continue

                file.write(line)

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
            processes.append(Popen(['tcpdump', '-i', 'eth0', 'udp', 'port %d' % port ,'-vv', '-X', '-Zroot', '-w %s' % pcap_file]))

            for process in processes:
                process.wait()
        except Exception as e:
            print(f"Error: {e}")
            for process in processes:
                process.terminate()
            exit(1)
