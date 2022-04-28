import logging
from typing import Tuple, Dict, List
import time
from collections import namedtuple

import zerorpc
import numpy as np

from uhd_wrapper.utils.config import RfConfig, RxStreamingConfig, TxStreamingConfig
from usrp_client.rpc_client import UsrpClient


LabeledUsrp = namedtuple(typename="LabeledUsrp", field_names="name ip client")


class System:
    syncThresholdSec = 0.2
    baseTimeOffsetSec = 0.2

    def __init__(self) -> None:
        self.__usrpClients: Dict[str, LabeledUsrp] = {}
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
        usrpName: str,
    ):
        self.__assertUniqueUsrp(ip, usrpName)

        usrpClient = self.createUsrpClient(ip)
        usrpClient.configureRfConfig(rfConfig)
        self.__usrpClients[usrpName] = LabeledUsrp(usrpName, ip, usrpClient)
        self.__usrpsSynced = False

    def __assertUniqueUsrp(self, ip: str, usrpName: str) -> None:
        if usrpName in self.__usrpClients.keys():
            raise ValueError("Connection to USRP already exists!")
        for usrp in self.__usrpClients.keys():
            if self.__usrpClients[usrp].ip == ip:
                raise ValueError("Connection to USRP already exists!")

    def __synchronizeUsrps(self) -> None:
        if not self.__usrpsSynced:
            for usrp in self.__usrpClients.keys():
                self.__usrpClients[usrp].client.setTimeToZeroNextPps()
                print("Set time to zero for PPS.")
            time.sleep(1.1)
            self.__usrpsSynced = True
            logging.info("Successfully synchronised USRPs...")

    def configureTx(self, usrpName: str, txStreamingConfig: TxStreamingConfig) -> None:
        self.__usrpClients[usrpName].client.configureTx(txStreamingConfig)
        logging.info(f"Configured TX Streaming for USRP: {usrpName}.")

    def configureRx(self, usrpName: str, rxStreamingConfig: RxStreamingConfig) -> None:
        self.__usrpClients[usrpName].client.configureRx(rxStreamingConfig)
        logging.info(f"Configured RX streaming for USRP: {usrpName}.")

    def execute(self) -> None:
        print("Synchronizing...")
        self.__synchronizeUsrps()
        self.__assertSynchronisationValid()
        baseTimeSec = self.__calculateBaseTimeSec()
        logging.info(f"Calling execution of usrps with base time: {baseTimeSec}")
        for usrpName in self.__usrpClients.keys():
            self.__usrpClients[usrpName].client.execute(baseTimeSec)

    def __calculateBaseTimeSec(self) -> float:
        currentFpgaTimesSec = self.__getCurrentFpgaTimes()
        logging.info(
            f"For calculating the base time, I received the following fpgaTimes: {currentFpgaTimesSec}"
        )
        maxTime = np.max(currentFpgaTimesSec)
        return maxTime + System.baseTimeOffsetSec

    def __getCurrentFpgaTimes(self) -> List[int]:
        return [
            item.client.getCurrentFpgaTime() for _, item in self.__usrpClients.items()
        ]

    def __assertSynchronisationValid(self) -> None:
        currentFpgaTimes = self.__getCurrentFpgaTimes()
        if (
            np.max(currentFpgaTimes) - np.min(currentFpgaTimes)
        ) > System.syncThresholdSec:
            raise ValueError(
                f"Fpga Times of USRPs mismatch... Synchronisation invalid."
            )

    def collect(self) -> Dict[str, List[np.ndarray]]:
        return {key: item.client.collect() for key, item in self.__usrpClients.items()}
