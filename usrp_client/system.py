import logging
from typing import Dict, List
import time
from collections import namedtuple

import zerorpc
import numpy as np

from uhd_wrapper.utils.config import RfConfig, RxStreamingConfig, TxStreamingConfig
from usrp_client.rpc_client import UsrpClient


LabeledUsrp = namedtuple("LabeledUsrp", "name ip client")


class System:
    """User interface for accessing multiple USRPs.

    This module is the main interface for using the USRP. A sysem is to be defined to which
    USRPs can be added. Using the system functions defined in the `System` class gives you
    direct access to the USRP configuration etc.

    Attrbiutes:
        syncThresholdSec(float): In order to verify if the USRPs in the system are properly
            synchronized, respective FPGA values are queried and compared. If the FPGA times
            differ more than `syncThresholdSec`, an exception is thrown that the USRPs are not
            synchronized. Default value: 0.2s.
        baseTimeOffsetSec(float): This value is taken for setting the same base time for all
            USRPs. For development use mainly. Do not change. Default value: 0.2s.
    """

    syncThresholdSec = 0.2
    baseTimeOffsetSec = 0.2

    def __init__(self) -> None:
        self.__usrpClients: Dict[str, LabeledUsrp] = {}
        self.__usrpsSynced = False

    def createUsrpClient(self, ip: str) -> UsrpClient:
        """Connect to the USRP server. Developers only.

        Args:
            ip (str): IP of the USRP.

        Returns:
            UsrpClient: RPC client for later use.
        """
        zeroRpcClient = zerorpc.Client()
        zeroRpcClient.connect(f"tcp://{ip}:5555")
        return UsrpClient(rpcClient=zeroRpcClient)

        # patch in test and check if called

    def addUsrp(
        self,
        rfConfig: RfConfig,
        ip: str,
        usrpName: str,
    ) -> None:
        """Add a new USRP to the system.

        Args:
            rfConfig (RfConfig): Configuration of the Radio Frontend.
            ip (str): IP of the USRP.
            usrpName (str): Identifier of the USRP to be added.
        """
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
        """Configure transmitter streaming.

        Use this function to configure the transmission streaming of your desired USRP.

        Args:
            usrpName (str): Identifier of USRP.
            txStreamingConfig (TxStreamingConfig): Desired configuration.
        """
        self.__usrpClients[usrpName].client.configureTx(txStreamingConfig)
        logging.info(f"Configured TX Streaming for USRP: {usrpName}.")

    def configureRx(self, usrpName: str, rxStreamingConfig: RxStreamingConfig) -> None:
        """Configure receiver streaming.

        Use this function to configure the receiving of your desired USRP.

        Args:
            usrpName (str): Identifier of USRP.
            rxStreamingConfig (RxStreamingConfig): Desired configuration.
        """
        self.__usrpClients[usrpName].client.configureRx(rxStreamingConfig)
        logging.info(f"Configured RX streaming for USRP: {usrpName}.")

    def getRfConfigs(self) -> Dict[str, RfConfig]:
        """Returns actual Radio Frontend configurations of the USRPs in the system.

        Returns:
            Dict[str, RfConfig]:
                Dict-keys denote the identifier/name of the USRPs.
                Values are the Radio Frontend configurations.
        """
        return {
            usrpName: self.__usrpClients[usrpName].client.getRfConfig()
            for usrpName in self.__usrpClients.keys()
        }

    def execute(self) -> None:
        """Executes all streaming configurations.

        Samples are buffered, timeouts are calculated, Usrps are synchronized...
        """
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
            f"For calculating the base time, I received the "
            f"following fpgaTimes: {currentFpgaTimesSec}"
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
            raise ValueError("Fpga Times of USRPs mismatch... Synchronisation invalid.")

    def collect(self) -> Dict[str, List[np.ndarray]]:
        """Collects the samples at each USRP.

        This is a blocking call. In the streaming configurations, the user defined when to send
        and receive the samples at which USRP. This method waits until all the samples are
        received (hence blocking) and returns them.

        Returns:
            Dict[str, List[np.ndarray]]:
                Dictionary containing the samples received.
                The key represents the usrp identifier.
        """
        return {key: item.client.collect() for key, item in self.__usrpClients.items()}
