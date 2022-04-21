from typing import Tuple, Dict
from collections import namedtuple

LabeledRpcClient = namedtuple("LabeledRpcClient", "label client")

import zerorpc

from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig


class System:
    def __init__(self) -> None:
        self.__rpcClients: Dict[str, Tuple[str, zerorpc.Client]] = dict()

    def addUsrp(self, rfConfig: RfConfig, ip: str, name: str, c: zerorpc.Client = None):
        if ip in self.__rpcClients.keys():
            raise ValueError("Connection to USRP already exists!")
        if c is None:
            c = zerorpc.Client()
        c.connect(f"tcp://{ip}:5555")
        c.configureRfConfig(rfConfig)
        self.__rpcClients[ip] = LabeledRpcClient(name, c)

        self.__synchronizeUsrps()

    def __synchronizeUsrps(self) -> None:
        for ip in self.__rpcClients.keys():
            self.__rpcClients[ip].client.setTimeToZeroNextPps()

    def configureTx(self, usrpName: str, txStreamingConfig: TxStreamingConfig) -> None:
        for ip in self.__rpcClients.keys():
            if self.__rpcClients[ip].label == usrpName:
                self.__rpcClients[ip].client.configureTx(txStreamingConfig)

    @property
    def rpcClients(self) -> Dict[str, Tuple[str, zerorpc.Client]]:
        return self.__rpcClients
