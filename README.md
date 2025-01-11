# quic vs mvfst
This repository contains the code for the quic vs mvfst project. The project aims to compare the performance of the QUIC and mvfst protocols. The code is written in Python.

## Setup Environment
To setup the environment, clone the repository and run the following commands:
```
cd <HOME>/docker_setup
chmod +x ./setup_env.sh
./setup_env.sh
```

## Test Suite
The test suite is located in the `sim` folder. To run the test suite, run the following commands:
```
cd <HOME>/sim
python3 test.py
```

## Collect Data
To automate the test suite and collect data, run the following commands:
```
cd <HOME>
python3 run_tests.py
```

## Process Data
To automate the data collection and processing, run the following commands:
```
cd <HOME>/output
python3 csv_parser.py
python3 pcap_parser.py
```

## Analyze Data
To analyze the data, run `<HOME>/output/CN_Graphs.ipynb` in Jupyter Notebook.

## Environment Variables
```TMP_FLDR=\<path\> #Temporary folder to store the data```
