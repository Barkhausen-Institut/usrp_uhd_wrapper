import sys
import os

#sys.path.extend([os.path.join("usrp_uhd_wrapper", "build", "lib")])

from uhd_wrapper.rpc_server.rpc_server import UsrpServer
import zerorpc
from uhd_wrapper.usrp_pybinding import Usrp, createUsrp

# create environment
PORT = 5555
IP_USRP = "localhost"
usrp = createUsrp(IP_USRP)

# start server
rpcServer = zerorpc.Server(UsrpServer(usrp))
rpcServer.bind(f"tcp://*:{PORT}")
rpcServer.run()

print(f"Created USRP server on IP {IP_USRP}, listening on port {PORT}")
