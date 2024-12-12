from subprocess import run, Popen, PIPE
from sim.get_files import SIM_FILES
from re import search
from os import path

source_dir = path.dirname(path.realpath(__file__))

def replace_env_links(i):
    env_file = path.join(source_dir, "sim", "src", "env.py")
    with open(env_file, "r", encoding="utf-8") as file:
        content = file.read()

    url, repl = "www.example.org", "www.google.com"
    t_url, t_repl = "demo.borland.com", "www.yahoo.com"
    if i % 2 == 0:
        url, repl = repl, url
        t_url, t_repl = t_repl, t_url

    content = content.replace(url, repl)
    content = content.replace(t_url, t_repl)
    with open(env_file, "w", encoding="utf-8") as file:
        file.write(content)

def get_data():
    l_d = [(0,0)]
    loss = [1, 5, 10]
    delay = [10, 50, 100, 200]
    for i in loss:
        for j in delay:
            l_d.append((i, j))

    l_d.reverse() # start w/ the slowest???
    t_p = [str(i) for i in range(2)] # enable or disable mode
    test_file = path.join(source_dir, "run_test.sh")
    success_csv = path.join(source_dir, "success.csv")
    fail_csv = path.join(source_dir, "fail.csv")
    run(['chmod', '+x', test_file])
    SIM_FILES()
    for i in range(2): # avoid pcap generation if you're going above 2
        ip = 6
        print(f"Running loop {i+1}")
        replace_env_links(i)
        for loss_vs_delay in l_d:
            for throughput in t_p:
                process = []
                process.append((Popen([test_file, str(loss_vs_delay[0]), str(loss_vs_delay[1])+"ms", throughput, str(i), "quic", str(ip), str(ip+1)], stdout=PIPE, stderr=PIPE, text=True), [loss_vs_delay, throughput, "quic"]))
                process.append((Popen([test_file, str(loss_vs_delay[0]), str(loss_vs_delay[1])+"ms", throughput, str(i), "mvfst", str(ip+2), str(ip+3)], stdout=PIPE, stderr=PIPE, text=True), [loss_vs_delay, throughput, "mvfst"]))
                ip += 6

                for proc, mode in process:
                    stdout, stderr = proc.communicate()

                    # instance, quic/mvfst - len = 6
                    # loss, int - % - len = 4
                    # delay, int ms - len = 6
                    curr_mode = "%-6s||%-4s||%-7s"%(mode[2], str(mode[0][0])+"%", str(mode[0][1])+"ms")
                    print(curr_mode)

                    pattern = r'(?s)\b(Normal Mode|Throughput Mode)\b.*'
                    match = search(pattern, stdout)
                    if match:
                        print(match.group(0))
                        with open(success_csv, "a") as file:
                            file.write(curr_mode+"\n")
                            file.write(match.group(0)+"\n")
                    else:
                        print("Some error occurred???")
                        print(f"Output from {mode[2]}:")
                        print(stdout)
                        print(f"Error from {mode[2]}:")
                        print(stderr)
                        print()
                        with open(fail_csv, "a") as file:
                            file.write(curr_mode+"\n")
                            file.write(mode[2]+"\n")
if __name__ == "__main__":
    get_data()
