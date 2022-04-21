from typing import Tuple, Dict

import zerorpc

from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig
from usrp_client.rpc_client import UsrpClient


class System:
    def __init__(self) -> None:
        self.__usrpClients: Dict[str, Tuple[str, UsrpClient]] = dict()

    def addUsrp(
        self,
        rfConfig: RfConfig,
        ip: str,
        name: str,
        clients: Tuple[zerorpc.Client, UsrpClient] = None,
    ):
        for usrp in self.__usrpClients.keys():
            if self.__usrpClients[usrp][0] == ip:
                raise ValueError("Connection to USRP already exists!")

        zeroRpcClient: zerorpc.Client
        usrpClient: UsrpClient

        if clients is None:
            zeroRpcClient = zerorpc.Client()
            usrpClient = UsrpClient(zeroRpcClient)
        else:
            zeroRpcClient = clients[0]
            usrpClient = clients[1]

        zeroRpcClient.connect(f"tcp://{ip}:5555")
        usrpClient.configureRfConfig(rfConfig)
        self.__usrpClients[name] = (ip, usrpClient)

        self.__synchronizeUsrps()

    def __synchronizeUsrps(self) -> None:
        for usrp in self.__usrpClients.keys():
            self.__usrpClients[usrp][1].setTimeToZeroNextPps()

    def configureTx(self, usrpName: str, txStreamingConfig: TxStreamingConfig) -> None:
        for usrp in self.__usrpClients.keys():
            if usrp == usrpName:
                self.__usrpClients[usrp][1].configureTx(txStreamingConfig)
