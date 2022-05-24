from uhd_wrapper.rpc_server.rpc_server import UsrpServer
import zerorpc
from uhd_wrapper.rpc_server.reconfigurable_usrp import ReconfigurableUsrp

# create environment
PORT = 5555
IP_USRP = "192.168.189.155"
usrp = ReconfigurableUsrp(IP_USRP)

# start server
rpcServer = zerorpc.Server(UsrpServer(usrp))
rpcServer.bind(f"tcp://*:{PORT}")
rpcServer.run()

print(f"Created USRP server on IP {IP_USRP}, listening on port {PORT}")
