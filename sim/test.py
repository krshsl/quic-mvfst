from src.utils import MyParser

if __name__ == "__main__":
    parser = MyParser(description = "Run sim suite to collect data")
    parser.add_argument("--mode", choices=["server", "client"], type = str,
                        help = "Select the mode to run (server/client)", default="server")
    parser.add_argument("--instance", choices=["quic", "mvfst"], type = str, help = "Select the instace to test", required=True)
    parser.add_argument("--host", type = str, metavar="host ip", help = "Input the server ip", required=True)
    parser.add_argument("--pcap_file", type = str, metavar="pcap file name", help = "Pcap File to save the server packet details.")
    parser.add_argument("--log", type=int, choices=[0,1,2], help="log level - 0: no stdout, 1: verbose, 2: print all", default=0)
    parser.add_argument("--throughput", type=int, choices=[0,1], help="Througput data collection : 0 - disabled, 1 - enabled", default=0)
    parser.add_argument("--no_dump", action=('store_true'), help="Add option to disable dump")

    # quic doesn't work well when 0-rtt is disabled!
    # parser.add_argument("--rtt_mode", type=int, choices=[0,1], help="Enable or Disable 0 RTT : 0 - disabled, 1 - enabled", default=1)
    args = parser.parse_args()
    if args.instance.lower() == "quic":
        from quic import CLIENT, SERVER
    elif args.instance.lower() == "mvfst":
        from mvfst import CLIENT, SERVER
    else:
        parser.error("error while parsing instance")

    if (args.mode == "client"):
        CLIENT(args).collect_client_data(args.instance.lower())
    else:
        SERVER(args).start_server()
        print("Please ensure you write into a new pcap file in next iter")
