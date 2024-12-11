from subprocess import run, Popen, PIPE
from sim.get_files import SIM_FILES
from re import search

l_d = [(0,0), (1,10), (5, 10), (1, 50), (5, 50), (1, 100), (5, 100)]
l_d.reverse() # start w/ the slowest???
t_p = [str(i) for i in range(2)] # enable or disable mode
rtt = "1" # better not to disable it!!
run(['chmod', '+x', 'run_test.sh'])
SIM_FILES()
for i in range(2): # run tests twice
    for loss_vs_delay in l_d:
        process = []
        ip = 6
        for throughput in t_p:
            process.append((Popen(['./run_test.sh', str(loss_vs_delay[0]), str(loss_vs_delay[1])+"ms", throughput, rtt, "quic", str(ip), str(ip+1)], stdout=PIPE, stderr=PIPE, text=True), [loss_vs_delay, throughput, "quic"]))
            process.append((Popen(['./run_test.sh', str(loss_vs_delay[0]), str(loss_vs_delay[1])+"ms", throughput, rtt, "mvfst", str(ip+2), str(ip+3)], stdout=PIPE, stderr=PIPE, text=True), [loss_vs_delay, throughput, "mvfst"]))
            ip += 6

            for proc, mode in process:
                stdout, stderr = proc.communicate()
                print(mode[2], "mode: loss, delay, tp, rtt::", str(mode[0][0]), str(mode[0][1])+"ms", mode[1], rtt)
                pattern = r'(?s)\b(Normal Mode|Throughput Mode)\b.*'
                match = search(pattern, stdout)
                if match:
                    print(match.group(0))
                else:
                    print("Some error occurred???")
                    print(f"Output from {mode[2]}:")
                    print(stdout)
                    print(f"Error from {mode[2]}:")
                    print(stderr)
                    print()
