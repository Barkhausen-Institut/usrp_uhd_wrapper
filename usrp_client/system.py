from email.mime import base
from typing import Tuple, Dict, List
import time

import zerorpc
import numpy as np

from uhd_wrapper.utils.config import RfConfig, RxStreamingConfig, TxStreamingConfig
from usrp_client.rpc_client import UsrpClient


class System:
    syncThresholdMs = 5.0
    baseTimeOffsetSec = 0.2

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
        if not self.__usrpsSynced:
            for usrp in self.__usrpClients.keys():
                self.__usrpClients[usrp][1].setTimeToZeroNextPps()
                print("Set time to zero for PPS.")
            time.sleep(1.1)
            self.__usrpsSynced = True
            print("Successfully synchronised USRPs...")

    def configureTx(self, usrpName: str, txStreamingConfig: TxStreamingConfig) -> None:
        self.__usrpClients[usrpName][1].configureTx(txStreamingConfig)
        print(f"Configured TX Streaming for USRP: {usrpName}.")

    def configureRx(self, usrpName: str, rxStreamingConfig: RxStreamingConfig) -> None:
        self.__usrpClients[usrpName][1].configureRx(rxStreamingConfig)
        print(f"Configured RX streaming for USRP: {usrpName}.")

    def execute(self) -> None:
        print("Synchronizing...")
        self.__synchronizeUsrps()
        self.__assertSynchronisationValid()
        baseTimeSec = self.__calculateBaseTimeSec()
        for usrpName in self.__usrpClients.keys():
            self.__usrpClients[usrpName][1].execute(baseTimeSec)

    def __calculateBaseTimeSec(self) -> float:
        currentFpgaTimesSec = self.__getCurrentFpgaTimes()
        maxTime = np.max(currentFpgaTimesSec)
        return maxTime + System.baseTimeOffsetSec

    def __getCurrentFpgaTimes(self) -> List[int]:
        return [item[1].getCurrentFpgaTime() for _, item in self.__usrpClients.items()]

    def __assertSynchronisationValid(self) -> None:
        currentFpgaTimes = self.__getCurrentFpgaTimes()
        if np.any(np.abs(np.diff(currentFpgaTimes)) > System.syncThresholdMs):
            raise ValueError("Fpga Times of USRPs mismatch... Synchronisation invalid.")

    def collect(self) -> List[List[np.array]]:
        return [item[1].collect() for _, item in self.__usrpClients.items()]
