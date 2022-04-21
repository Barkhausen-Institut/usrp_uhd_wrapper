from typing import Tuple, Dict, List
import time

import zerorpc
import numpy as np

from uhd_wrapper.utils.config import RfConfig, RxStreamingConfig, TxStreamingConfig
from usrp_client.rpc_client import UsrpClient


class System:
    syncThresholdMs = 5.0

    def __init__(self) -> None:
        self.__usrpClients: Dict[str, Tuple[str, UsrpClient]] = dict()
        self.__usrpsSynced = False

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
        self.__usrpsSynced = False

    def __synchronizeUsrps(self) -> None:
        for usrp in self.__usrpClients.keys():
            self.__usrpClients[usrp][1].setTimeToZeroNextPps()

    def configureTx(self, usrpName: str, txStreamingConfig: TxStreamingConfig) -> None:
        self.__usrpClients[usrpName][1].configureTx(txStreamingConfig)

    def configureRx(self, usrpName: str, rxStreamingConfig: RxStreamingConfig) -> None:
        self.__usrpClients[usrpName][1].configureRx(rxStreamingConfig)

    def execute(self) -> None:
        if not self.__usrpsSynced:
            self.__synchronizeUsrps()
            self.__usrpsSynced = True

        self.__assertSynchronisationValid()
        for usrpName in self.__usrpClients.keys():
            self.__usrpClients[usrpName][1].execute(0.0)

    def __assertSynchronisationValid(self) -> None:
        time.sleep(1.1)  # sleep to make sure that pps is locked
        fpgaTimes = [
            item[1].getCurrentFpgaTime() for _, item in self.__usrpClients.items()
        ]

        if np.any(np.abs(np.diff(fpgaTimes)) > System.syncThresholdMs):
            raise ValueError("Fpga Times of USRPs mismatch... Synchronisation invalid.")

    def collect(self) -> List[List[np.array]]:
        return [item[1].collect() for _, item in self.__usrpClients.items()]
