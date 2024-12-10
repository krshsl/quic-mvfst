from src.arg_parser import MyParser

if __name__ == "__main__":
    parser = MyParser(description = "Run sim suite to collect data")
    parser.add_argument("--mode", choices=["server", "client"], type = str,
                        help = "Select the mode to run (server/client)", default="server")
    parser.add_argument("--instance", choices=["quic", "mvfst"], type = str, help = "Select the instace to test", required=True)
    parser.add_argument("--host", type = str, help = "Input the server ip", required=True)
    parser.add_argument("--pcap_file", type = str, help = "Pcap File to save the server packet details.")
    parser.add_argument("--debug", type=bool, help="Enable to Debug output (default=False)", default=False)
    parser.add_argument("--rtt_mode", type=bool, help="Enable/Disable 0-rtt (default=True)", default=True)
    args = parser.parse_args()
    if args.instance.lower() == "quic":
        from quic import CLIENT, SERVER
    elif args.instance.lower() == "mvfst":
        from mvfst import CLIENT, SERVER
    else:
        parser.error("error while parsing instance")

    if (args.mode == "client"):
        CLIENT(args.host, args.rtt_mode, args.debug).collect_client_data()
    else:
        if not (args.pcap_file):
            parser.error("Pcap_file missing")

        SERVER(args.host, args.pcap_file, args.debug).start_server()
        print("Please ensure you write into a new pcap file in next iter")
