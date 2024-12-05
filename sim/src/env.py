from os import path, makedirs
from urllib.request import urlopen
from shutil import rmtree

MVFST_PKG :str = "/vcpkg/packages/proxygen_x64-linux/tools/proxygen/hq"
CHROME_PKG :str = ""
SIM_DIR :str = "./quic"
SIM_FILE :str = "index.html"
SIM_URL :str = "www.example.org"
OUT_DIR :str = "out"
HANDSHAKE: str = "handshake"
RTT: str = "rtt"
RTT_ITERS: int = 50

class RUN_SIM:
    def __init__(self, host):
        self.host = host
        self._create_root_folder()
        self._download_files()

    def _rm_mk_dir(self, dir):
        if path.exists(dir):
            rmtree(dir)

        makedirs(dir)

    def _create_root_folder(self):
        self.sim_dir = path.join(SIM_DIR, SIM_URL)
        self._rm_mk_dir(self.sim_dir)

        self.out_dir = path.join(SIM_DIR, OUT_DIR)
        self._rm_mk_dir(self.out_dir)

    def _download_files(self):
        with urlopen("http://"+SIM_URL) as webpage:
            content = webpage.read().decode()

        self.sim_file = path.join(self.sim_dir, SIM_FILE)
        with open(self.sim_file, 'w') as output:
            output.write(content)
