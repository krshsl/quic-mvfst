from argparse import ArgumentParser
from sys import stderr, exit

class MyParser(ArgumentParser):
    def error(self, message):
        stderr.write('error: %s\n' % message)
        self.print_help()
        exit(2)
