from tempfile import TemporaryDirectory
from os import path
from urllib.request import urlopen


MVFST_PKG :str = "/vcpkg/packages/proxygen_x64-linux/tools/proxygen/hq"
CHROME_PKG :str = ""
SIM_DIR :str = "quic"
SIM_FILE :str = "index.html" # ~ 1kb
SIM_URL :str = "www.example.org"
OUT_DIR :str = "out"
HANDSHAKE: str = "handshake"
RTT: str = "rtt"
RTT_ITERS: int = 128

class RUN_SIM:
    def __init__(self, host):
        self.host = host
        self._create_root_folder()
        self._download_files()

    def _create_root_folder(self):
        self.sim_dir = TemporaryDirectory(prefix=SIM_DIR)
        self.out_dir = TemporaryDirectory(prefix=OUT_DIR, dir=self.sim_dir.name)

    def _download_files(self):
        with urlopen("http://"+SIM_URL) as webpage:
            content = webpage.read().decode()

        self.sim_file = path.join(self.sim_dir.name, SIM_FILE)
        with open(self.sim_file, 'w') as output:
            output.write(content)
