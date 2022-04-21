from typing import List, Tuple, Dict

import zerorpc

from uhd_wrapper.utils.config import RfConfig


class System:
    def __init__(self) -> None:
        self.__rpcClients: Dict[str, Tuple[str, zerorpc.Client]] = dict()

    def addUsrp(self, rfConfig: RfConfig, ip: str, name: str):
        if ip in self.__rpcClients.keys():
            raise ValueError("Connection to USRP already exists!")
        c = zerorpc.Client()
        c.connect(f"tcp://{ip}:5555")
        self.__rpcClients[ip] = (name, c)

    @property
    def rpcClients(self) -> Dict[str, Tuple[str, zerorpc.Client]]:
        return self.__rpcClients
