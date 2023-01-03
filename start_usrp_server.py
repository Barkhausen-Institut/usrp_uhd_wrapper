import argparse

from uhd_wrapper.rpc_server.rpc_server import UsrpServer
import zerorpc
from uhd_wrapper.rpc_server.reconfigurable_usrp import MimoReconfiguringUsrp

def parseArgs():
    parser = argparse.ArgumentParser(description="Start the USRP RPC server")
    parser.add_argument("--uhd-ip", type=str, default="localhost", help="Determine the IP of the USRP to connect to")

    return parser.parse_args()

# create environment
PORT = 5555
IP_USRP = parseArgs().uhd_ip
usrp = MimoReconfiguringUsrp(IP_USRP)

# start server
rpcServer = zerorpc.Server(UsrpServer(usrp))
rpcServer.bind(f"tcp://*:{PORT}")
rpcServer.run()

print(f"Created USRP server on IP {IP_USRP}, listening on port {PORT}")
