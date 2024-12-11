#!/bin/bash
if [[ $value -gt 0 ]]; then
    sudo tc qdisc add dev eth0 root netem loss $1
fi
cd /sim
python3 /sim/test.py --throughput=$2 --rtt_mode=$3 --pcap_file=$6\/$4 --host=$5 --mode=server --instance=$6
