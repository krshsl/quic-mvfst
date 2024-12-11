#!/bin/bash
if [[ $1 -gt 0 ]]; then
    sudo tc qdisc add dev eth0 root netem delay $2 loss $1%
    sudo tc qdisc show dev eth0
fi
cd /sim
python3 /sim/test.py --throughput=$3 --pcap_file=/$6\/$4 --host=$5 --mode=server --instance=$6
