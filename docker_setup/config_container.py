from argparse import ArgumentParser
from io import StringIO
from json import loads
from subprocess import run
from sys import stderr, exit

class MyParser(ArgumentParser):
    def error(self, message):
        stderr.write('error: %s\n' % message)
        self.print_help()
        exit(2)

configs = ['start', 'stop']
images = ['proxygen:cn', 'quic:cn']

def config_container(mode):
    containers = run(['docker', 'ps', '-a', '--format=json'], capture_output=True, text=True)
    containers = StringIO(containers.stdout)
    for c in containers:
            name = loads(c)['Names']
            run(['docker', mode, name])
            print("%s %sed" % (name, mode))


if __name__ == "__main__":
    parser = MyParser(description = "Start/Stop all QUIC containers")
    parser.add_argument("mode", choices=["start", "stop"], type = str,
                        help = "Configures the mode to start or stop a container")
    args = parser.parse_args()
    config_container(args.mode)
