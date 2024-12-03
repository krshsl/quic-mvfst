from io import StringIO
from json import loads
from subprocess import run
from sys import exit

configs = ['start', 'stop']
# images = ['proxygen:cn', 'mvfst:cn', 'quic:cn']
images = ['proxygen:cn', 'quic:cn']

def get_containers():
    containers = run(['docker', 'ps', '-a', '--format=json'], capture_output=True, text=True)
    containers = StringIO(containers.stdout)
    names = []
    for c in containers:
        names.append(loads(c)['Names'])
    return names

def exec_container(name):
    run(['docker', 'start', name])
    run(['docker', 'exec', '-it', name, '/bin/bash'])


if __name__ == "__main__":
    names = get_containers()
    cli_out = ""
    for i, name in enumerate(names):
        cli_out += "%d::%s\n" % (i+1, name)
    cli_out += "%d::Exit" % (len(names)+1)

    while(True):
        try:
            print(cli_out)
            option = input("Select the docker to start running or enter %s to exit:" % (len(names)+1))
            if option.isnumeric():
                option = int(option)
                option -= 1
                if option >= 0 and option <= len(names):
                    if option != len(names):
                        exec_container(names[option])
                    else:
                        print("exit")
                    exit(0)
        except (KeyboardInterrupt, EOFError):
            print("\nexit")
            exit(0)
