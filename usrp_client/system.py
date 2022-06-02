import logging
from typing import Dict, List
import time
from collections import namedtuple
from threading import Timer

import zerorpc
import numpy as np

from uhd_wrapper.utils.config import (
    MimoSignal,
    containsClippedValue,
    RfConfig,
    RxStreamingConfig,
    TxStreamingConfig,
)
from usrp_client.rpc_client import UsrpClient


LabeledUsrp = namedtuple("LabeledUsrp", "name ip client")


class System:
    """User interface for accessing multiple USRPs.

    This module is the main interface for using the USRP. A system is to be defined to which
    USRPs can be added. Using the system functions defined in the `System` class gives you
    direct access to the USRP configuration etc.

    Attributes:
        syncThresholdSec(float): In order to verify if the USRPs in the system are properly
            synchronized, respective FPGA values are queried and compared. If the FPGA times
            differ more than `syncThresholdSec`, an exception is thrown that the USRPs are not
            synchronized. Default value: 0.2s.
        baseTimeOffsetSec(float): This value is taken for setting the same base time for all
            USRPs. For development use mainly. Do not change. Default value: 0.2s.
        syncAttempts (int): Specifies number of synchronization attemps for USRP system.
        timeBetweenSyncAttempts (float): Sleep time between two synchronisation attempts in s.
        syncTimeOut (float): Timeout of synchronisation.
    """

    syncThresholdSec = 0.2
    baseTimeOffsetSec = 0.2
    syncAttempts = 3
    timeBetweenSyncAttempts = 0.3
    syncTimeOut = 1.0

    def __init__(self) -> None:
        self._usrpClients: Dict[str, LabeledUsrp] = {}
        self._usrpsSynced = False

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
        self._usrpsSynced = False
        self._assertUniqueUsrp(ip, usrpName)

        usrpClient = self.createUsrpClient(ip)
        usrpClient.configureRfConfig(rfConfig)
        usrpClient.resetStreamingConfigs()
        self._usrpClients[usrpName] = LabeledUsrp(usrpName, ip, usrpClient)

    def _assertUniqueUsrp(self, ip: str, usrpName: str) -> None:
        self._assertUniqueUsrpName(usrpName)
        self._assertUniqueIp(ip)

    def _assertUniqueUsrpName(self, usrpName: str) -> None:
        if usrpName in self._usrpClients.keys():
            raise ValueError("Connection to USRP already exists!")

    def _assertUniqueIp(self, ip: str) -> None:
        for usrp in self._usrpClients.keys():
            if self._usrpClients[usrp].ip == ip:
                raise ValueError("Connection to USRP already exists!")

    def configureTx(self, usrpName: str, txStreamingConfig: TxStreamingConfig) -> None:
        """Configure transmitter streaming.

        Use this function to configure the transmission streaming of your desired USRP.

        Args:
            usrpName (str): Identifier of USRP.
            txStreamingConfig (TxStreamingConfig): Desired configuration.
        """
        self._usrpClients[usrpName].client.configureTx(txStreamingConfig)
        logging.info(f"Configured TX Streaming for USRP: {usrpName}.")

    def configureRx(self, usrpName: str, rxStreamingConfig: RxStreamingConfig) -> None:
        """Configure receiver streaming.

        Use this function to configure the receiving of your desired USRP.

        Args:
            usrpName (str): Identifier of USRP.
            rxStreamingConfig (RxStreamingConfig): Desired configuration.
        """
        self._usrpClients[usrpName].client.configureRx(rxStreamingConfig)
        logging.info(f"Configured RX streaming for USRP: {usrpName}.")

    def getRfConfigs(self) -> Dict[str, RfConfig]:
        """Returns actual Radio Frontend configurations of the USRPs in the system.

        Returns:
            Dict[str, RfConfig]:
                Dict-keys denote the identifier/name of the USRPs.
                Values are the Radio Frontend configurations.
        """
        return {
            usrpName: self._usrpClients[usrpName].client.getRfConfig()
            for usrpName in self._usrpClients.keys()
        }

    def execute(self) -> None:
        """Executes all streaming configurations.

        Samples are buffered, timeouts are calculated, Usrps are synchronized...
        """
        self._synchronizeUsrps()
        baseTimeSec = self._calculateBaseTimeSec()
        logging.info(f"Calling execution of usrps with base time: {baseTimeSec}")
        for usrpName in self._usrpClients.keys():
            self._usrpClients[usrpName].client.execute(baseTimeSec)

    def _synchronizeUsrps(self) -> None:
        syncAttempts = 1
        if not self._usrpsSynced:
            while (
                syncAttempts <= System.syncAttempts and not self.synchronisationValid()
            ):
                self._setTimeToZeroNextPps()
                self.sleep(System.timeBetweenSyncAttempts)
                syncAttempts += 1

        if syncAttempts > System.syncAttempts:
            raise RuntimeError(
                f"Tried at least {self.syncAttempts} syncing wihout succes."
            )
        self._startResetSyncFlagTimer()
        self._usrpsSynced = True

    def _startResetSyncFlagTimer(self) -> None:
        def resetSyncFlag() -> None:
            self._usrpsSynced = False

        resetSyncFlagTimer = Timer(self.syncTimeOut, resetSyncFlag)
        resetSyncFlagTimer.daemon = True
        resetSyncFlagTimer.start()

    def synchronisationValid(self) -> bool:
        currentFpgaTimes = self._getCurrentFpgaTimes()
        return (
            np.max(currentFpgaTimes) - np.min(currentFpgaTimes)
            < System.syncThresholdSec
        )

    def _setTimeToZeroNextPps(self) -> None:
        for usrp in self._usrpClients.keys():
            self._usrpClients[usrp].client.setTimeToZeroNextPps()
            logging.info("Set time to zero for PPS.")
        self.sleep(1.1)

    def sleep(self, delay: float) -> None:
        time.sleep(delay)

    def _calculateBaseTimeSec(self) -> float:
        currentFpgaTimesSec = self._getCurrentFpgaTimes()
        logging.info(
            f"For calculating the base time, I received the "
            f"following fpgaTimes: {currentFpgaTimesSec}"
        )
        maxTime = np.max(currentFpgaTimesSec)
        return maxTime + System.baseTimeOffsetSec

    def _getCurrentFpgaTimes(self) -> List[int]:
        return [
            item.client.getCurrentFpgaTime() for _, item in self._usrpClients.items()
        ]

    def collect(self) -> Dict[str, List[MimoSignal]]:
        """Collects the samples at each USRP.

        This is a blocking call. In the streaming configurations, the user defined when to send
        and receive the samples at which USRP. This method waits until all the samples are
        received (hence blocking) and returns them.

        Returns:
            Dict[str, List[MimoSignal]]:
                Dictionary containing the samples received.
                The key represents the usrp identifier.
        """
        samples = {
            key: item.client.collect() for key, item in self._usrpClients.items()
        }
        self._assertNoClippedValues(samples)
        return samples

    def getSupportedSamplingRates(self, usrpName: str) -> np.ndarray:
        """Returns supported sampling rates.

        Args:
            usrpName (str): Identifier of USRP to be queried.

        Returns:
            np.ndarray: Array of supported sampling rates.
        """
        return self._usrpClients[usrpName].client.getSupportedSamplingRates()

    def _assertNoClippedValues(self, samples: Dict[str, List[MimoSignal]]) -> None:
        for usrpName, usrpConfigSamples in samples.items():
            if any(
                containsClippedValue(mimoSignal) for mimoSignal in usrpConfigSamples
            ):
                raise ValueError(
                    f"USRP {usrpName} contains clipped values. Please check your gains."
                )
