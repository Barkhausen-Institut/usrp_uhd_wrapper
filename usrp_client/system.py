from typing import Tuple, Dict

import zerorpc

from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig


class System:
    def __init__(self) -> None:
        self.__rpcClients: Dict[str, Tuple[str, zerorpc.Client]] = dict()

    def addUsrp(self, rfConfig: RfConfig, ip: str, name: str, c: zerorpc.Client = None):
        for usrp in self.__rpcClients.keys():
            if self.__rpcClients[usrp][0] == ip:
                raise ValueError("Connection to USRP already exists!")

        if c is None:
            c = zerorpc.Client()
        c.connect(f"tcp://{ip}:5555")
        c.configureRfConfig(rfConfig)
        self.__rpcClients[name] = (ip, c)

        self.__synchronizeUsrps()

    def __synchronizeUsrps(self) -> None:
        for usrp in self.__rpcClients.keys():
            self.__rpcClients[usrp][1].setTimeToZeroNextPps()

    def configureTx(self, usrpName: str, txStreamingConfig: TxStreamingConfig) -> None:
        for usrp in self.__rpcClients.keys():
            if usrp == usrpName:
                self.__rpcClients[usrp][1].configureTx(txStreamingConfig)
