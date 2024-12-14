from subprocess import run, CalledProcessError
from multiprocessing import Pool, cpu_count
from argparse import ArgumentParser
from os import sep, walk, path
from csv import DictWriter

import numpy as np

class MyParser(ArgumentParser):
    def error(self, message):
        stderr.write('error: %s\n' % message)
        self.print_help()
        exit(2)

def parse_tshark_output(args):
    pcap_file = args[0]
    output = args[1]
    options = {
        "total": [],
        "dropped": [ "-T", "fields", "-e", "quic.packet_number"],
        "jitter": ["-T", "fields", "-e", "frame.time_relative"]
    }
    try:
        tshark = [
            "tshark", "-nr", pcap_file
        ]
        final= 0
        for key, value in options.items():
            command = tshark+value
            print(" ".join(command))
            if key == "jitter":
                result = run(command, capture_output=True, text=True)
                result = [float(line.strip()) for line in result.stdout.splitlines()]
                result.sort()
                interarrival_times = np.diff(result)
                jitter = np.mean(np.abs(interarrival_times - np.mean(interarrival_times)))
                output["mean_jitter"] = jitter
                output["std_jitter"] = np.std(result)
                jitter = 0
                for i in range(1, len(result)):
                    jitter += abs(result[i] - jitter) / 16
                output["calc_jitter"] = jitter
                jitter = sum(interarrival_times)/(output["total"]-output["dropped"])
                output["avg_jitter"] = jitter
                output[key] = result
            else:
                result = run(command, capture_output=True, text=True)
                output[key] = len(result.stdout)

        return output
    except CalledProcessError as e:
        print(f"Error running tshark: {e}")
        return {}


def get_url(parts):
    if int(parts[1]):
        return "www.yahoo.com" if int(parts[4]) else  "www.google.com"
    else:
        return "demo.borland.com" if int(parts[4]) else  "www.example.org"

def extract_folder_info(file, root_folder):
    """Extracts metadata from the folder path relative to the root."""
    parts = path.relpath(file, root_folder).split(sep)
    folder_info = {
        "Protocol": parts[0],
        "url": get_url(parts),
        "Throughput": int(parts[4]),
        "LossP": int(parts[2]),
        "Delay": parts[3],
    }
    return folder_info

def collect_file_paths(root_folder):
    file_paths = []
    for dirpath, _, filenames in walk(root_folder):
        for filename in filenames:
            file_path = path.join(dirpath, filename)
            if file_path.endswith(".pcap"):
                folder_info = extract_folder_info(dirpath, root_folder)
                file_paths.append((file_path, folder_info))
    
    return file_paths

def collect_files_data(root_folder):
    """Collects data from files and their folder metadata."""
    mvfst, quic = [], []
    args = collect_file_paths(root_folder)
    if not args:
        return

    with Pool(cpu_count()) as p:
        output = p.map(parse_tshark_output, args)
        for info in output:
            if "mvfst" in info["Protocol"]:
                mvfst.append(info)
            else:
                quic.append(info)

    return {"mvfst": mvfst, "quic": quic}

def dict_list_to_csv_string(dict_list):
    if not dict_list:
        print("The list is empty.")
        return ""

    for key, value in dict_list.items():
        output_file = key + "_pcap.csv"
        with open(output_file, mode="w", newline="") as csvfile:
            fieldnames = value[0].keys()
            writer = DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(value)

if __name__ == "__main__":
    parser = MyParser(description = "Run file to parse pcap file(s)")
    parser.add_argument("--folder", type = str,
                        help = "Enter the folder to search the files in")
    data = collect_files_data(parser.parse_args().folder)
    dict_list_to_csv_string(data)
