import sys
import os

sys.path.extend([os.path.join("build", "lib"), os.path.join("release_build", "lib")])

from server.rpc_server import UsrpServer
import zerorpc
from usrp_pybinding import Usrp, createUsrp

# create environment
PORT = 5555
IP_SERVER = "localhost"
usrp = createUsrp(IP_SERVER)

# start server
rpcServer = zerorpc.Server(UsrpServer(usrp))
rpcServer.bind(f"tcp://*:{PORT}")
rpcServer.run()

print(f"Created USRP server on IP {IP_SERVER}, listening on port {PORT}")
