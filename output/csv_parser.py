import os
import csv

def process_data(input_file, quic_file, mvfst_file):
    # Read the raw content from the input file
    with open(input_file, 'r') as file:
        raw_content = file.readlines()

    # Initialize variables to store processed data
    quic_data = []
    mvfst_data = []

    current_protocol = None
    packet_loss = None
    delay = None
    mode = None

    # Process each line in the raw content
    i = 0
    while i < len(raw_content):
        line = raw_content[i].strip()
        if not line:  # Skip empty lines
            i += 1
            continue

        if "quic" in line and "||" in line:  # Start of a QUIC block
            current_protocol = "quic"
            parts = line.split("||")
            if len(parts) >= 3:
                packet_loss = parts[1].strip()
                delay = parts[2].strip()
        elif "mvfst" in line and "||" in line:  # Start of an MVFST block
            current_protocol = "mvfst"
            parts = line.split("||")
            if len(parts) >= 3:
                packet_loss = parts[1].strip()
                delay = parts[2].strip()
        elif "Normal Mode" or "Throughput Mode" in line: # normal is always followed by throughput!!
            mode = line.strip()
            i += 2

            # Process handshake data
            handshake_line = raw_content[i].strip()
            parts = handshake_line.split("||")
            if len(parts) >= 6 and parts[1]=="hnsk":
                url = parts[2].strip()
                size = parts[3].strip()
                status = parts[4].strip()
                time = parts[5].strip()
                handshake_row = [packet_loss, delay, mode, "handshake", url, size, status, time, "", "", ""]
                if current_protocol == "quic":
                    quic_data.append(handshake_row)
                elif current_protocol == "mvfst":
                    mvfst_data.append(handshake_row)

            i += 2
            # Process RTT data
            rtt_line = raw_content[i].strip()
            parts = rtt_line.split("||")
            if len(parts) >= 9 and "rtt" in parts[1]:
                url = parts[2].strip()
                size = parts[3].strip()
                status = parts[4].strip()
                time = parts[5].strip()
                rtt_count = parts[6].strip()
                fail_count = parts[7].strip()
                time_list = parts[8].strip()
                rtt_row = [packet_loss, delay, mode, "rtt", url, size, status, time, rtt_count, fail_count, time_list]
                if current_protocol == "quic":
                    quic_data.append(rtt_row)
                elif current_protocol == "mvfst":
                    mvfst_data.append(rtt_row)

        i += 1

    headers = [
        "Packet Loss", "Delay", "Mode", "Type", "URL",
        "Size", "Status", "Time", "RTT Count", "Fail Count", "Time List"
    ]

    with open(quic_file, 'w', newline='') as quic_output:
        writer = csv.writer(quic_output)
        writer.writerow(headers)
        writer.writerows(quic_data)

    with open(mvfst_file, 'w', newline='') as mvfst_output:
        writer = csv.writer(mvfst_output)
        writer.writerow(headers)
        writer.writerows(mvfst_data)


input_file = "success.csv"
quic_file = "quic_data.csv"
mvfst_file = "mvfst_data.csv"
process_data(input_file, quic_file, mvfst_file)
print(f"QUIC data saved to {os.path.abspath(quic_file)}")
print(f"MVFST data saved to {os.path.abspath(mvfst_file)}")
