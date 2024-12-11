from src.utils import MyParser
from subprocess import run
from src.env import INTERFACE

if __name__ == "__main__":
    parser = MyParser(description = "Run sim suite to collect data")

    parser.add_argument("--loss", type = int, help = "Input the loss %", required=True)
    args = parser.parse_args()
    run(["sudo","tc","qdisc","del","dev",INTERFACE,"root"])
    run(["sudo","tc","qdisc","add","dev",INTERFACE,"root","netem","loss",args.loss])
