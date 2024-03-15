import argparse

from uhd_wrapper.rpc_server.rpc_server import UsrpServer
import zerorpc
from uhd_wrapper.rpc_server.reconfigurable_usrp import RestartingUsrp


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the USRP RPC server")
    parser.add_argument("--uhd-ip", type=str, default="localhost",
                        help="Determine the IP of the USRP to connect to")
    parser.add_argument("--rpc-port", type=int, default=5555,
                        help="Port where the RPC server listens to")
    parser.add_argument("--usrp-type", type=str, default="x410",
                        help="Type of USRP to be expected")
    parser.add_argument("--master-clock-rate", type=float, default=0,
                        help="Master Clock Rate to configure. "
                             "Leave empty or set 0 to leave unchanged.")

    return parser.parse_args()


# create environment
args = parseArgs()
IP_USRP = args.uhd_ip
PORT = args.rpc_port
TYPE = args.usrp_type

usrp = RestartingUsrp.create(IP_USRP, 
                             desiredDeviceType=TYPE, 
                             masterClockRate=args.master_clock_rate)

# start server
rpcServer = zerorpc.Server(UsrpServer(usrp))
rpcServer.bind(f"tcp://*:{PORT}")
rpcServer.run()

print(f"Created USRP server on IP {IP_USRP}, listening on port {PORT}")
