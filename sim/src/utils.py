from argparse import ArgumentParser
from math import floor, log10
from sys import stderr, exit

class MyParser(ArgumentParser):
    def error(self, message):
        stderr.write('error: %s\n' % message)
        self.print_help()
        exit(2)


class H_Test:
    def __init__(self, time, status):
        self.time = time
        self.status = status
        self.d = "||" # delimitter

    def round_impl(self, n, sig_digits=10):
        if n == 0:
            return 0
        else:
            return round(n, sig_digits - int(floor(log10(abs(n)))) - 1)

    def show_data(self, instance, url, size):
        # instance, quic/mvfst - len = 6
        # mode, hnsk - len = 4
        # url, str - len = 20 (assign max len of your url)
        # size(KB), int.float - len = 10 - round_impl
        # status, int/bool - len = 6
        # time, int/float - len = 10 - use round_impl
        p_format = f"%-6s{self.d}%-4s{self.d}%-20s{self.d}%-10s{self.d}%-6s{self.d}%-10s" # delimitter
        print(p_format % ("instce", "mode", "url", "size(KB)", "status", "time"))
        print(p_format % (instance, "hnsk", url, size, self.status, self.time))


class R_Test(H_Test):
    def __init__(self, time, status, time_list, fail_cnt, rtt_cnt):
        super().__init__(time, status)
        self.fail_cnt = fail_cnt
        self.rtt_cnt = rtt_cnt
        self.time_list = []
        for curr_time in time_list:
            if isinstance(curr_time, list):
                self.time_list.extend(curr_time)
            else:
                self.time_list.append(curr_time)

    def show_data(self, instance, url, size):
        # instance, quic/mvfst - len = 6
        # mode, rtt - len = 4
        # size(KB), int.float - len = 10 - round_impl
        # status, int/bool - len = 6
        # time, int/float - len = 10 - use round_impl
        # rtt_cnt, int/float - len = 10 - use round_impl
        # fail_cnt, int/float - len = 10 - use round_impl
        # time_list, list - ensure it is the last item so len can be any!
        p_format = f"%-6s{self.d}%-4s{self.d}%-20s{self.d}%-10s{self.d}%-6s{self.d}%-10s{self.d}%-10s{self.d}%-10s{self.d}%s" # delimitter
        print(p_format % ("instce", "mode", "url", "size(KB)", "status", "time", "rtt_count", "fail_cnt", "time_list"))
        print(p_format % (instance, "rtt", url, size, self.status, self.time, self.rtt_cnt, self.fail_cnt, self.time_list))
