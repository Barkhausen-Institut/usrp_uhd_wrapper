from typing import Tuple, Dict

import zerorpc

from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig
from usrp_client.rpc_client import UsrpClient


class System:
    def __init__(self) -> None:
        self.__usrpClients: Dict[str, Tuple[str, UsrpClient]] = dict()

    def createUsrpClient(self, ip: str) -> UsrpClient:
        zeroRpcClient = zerorpc.Client()
        zeroRpcClient.connect(f"tcp://{ip}:5555")
        return UsrpClient(rpcClient=zeroRpcClient)

        # patch in test and check if called

    def addUsrp(
        self,
        rfConfig: RfConfig,
        ip: str,
        name: str,
    ):
        for usrp in self.__usrpClients.keys():
            if self.__usrpClients[usrp][0] == ip:
                raise ValueError("Connection to USRP already exists!")

        usrpClient = self.createUsrpClient(ip)
        usrpClient.configureRfConfig(rfConfig)
        self.__usrpClients[name] = (ip, usrpClient)

    def __synchronizeUsrps(self) -> None:
        for usrp in self.__usrpClients.keys():
            self.__usrpClients[usrp][1].setTimeToZeroNextPps()

    def configureTx(self, usrpName: str, txStreamingConfig: TxStreamingConfig) -> None:
        self.__usrpClients[usrpName][1].configureTx(txStreamingConfig)
