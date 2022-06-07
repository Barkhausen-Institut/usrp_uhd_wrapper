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


class TimedFlag:
    """Creates a flag that is reset after a certain time denoted by `resetTimeSec`."""

    def __init__(self, resetTimeSec: float) -> None:
        self._resetTimeSec = resetTimeSec
        self._value = False
        self.__resetSyncFlagTimer = Timer(10.0, lambda: None)

    def set(self) -> None:
        """Sets the flag and resets after the specified time."""
        self._value = True
        self._startTimer()

    def reset(self) -> None:
        """Reset flag."""
        self._value = False

    def _startTimer(self) -> None:
        def setFlagToFalse() -> None:
            self._value = False

        self.__resetSyncFlagTimer.cancel()
        self.__resetSyncFlagTimer = Timer(self._resetTimeSec, setFlagToFalse)
        self.__resetSyncFlagTimer.daemon = True
        self.__resetSyncFlagTimer.start()

    def isSet(self) -> bool:
        """Returns the value of the flag."""
        return self._value


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
    syncTimeOut = 20 * 60.0  # every 20 minutes

    def __init__(self) -> None:
        self.__usrpClients: Dict[str, LabeledUsrp] = {}
        self._usrpsSynced = TimedFlag(resetTimeSec=System.syncTimeOut)

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
        self._usrpsSynced.reset()
        self.__assertUniqueUsrp(ip, usrpName)

        usrpClient = self.createUsrpClient(ip)
        usrpClient.configureRfConfig(rfConfig)
        usrpClient.resetStreamingConfigs()
        self.__usrpClients[usrpName] = LabeledUsrp(usrpName, ip, usrpClient)

    def __assertUniqueUsrp(self, ip: str, usrpName: str) -> None:
        self.__assertUniqueUsrpName(usrpName)
        self.__assertUniqueIp(ip)

    def __assertUniqueUsrpName(self, usrpName: str) -> None:
        if usrpName in self.__usrpClients.keys():
            raise ValueError("Connection to USRP already exists!")

    def __assertUniqueIp(self, ip: str) -> None:
        for usrp in self.__usrpClients.keys():
            if self.__usrpClients[usrp].ip == ip:
                raise ValueError("Connection to USRP already exists!")

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
        self.__synchronizeUsrps()
        baseTimeSec = self.__calculateBaseTimeSec()
        logging.info(f"Calling execution of usrps with base time: {baseTimeSec}")
        for usrpName in self.__usrpClients.keys():
            self.__usrpClients[usrpName].client.execute(baseTimeSec)

    def __synchronizeUsrps(self) -> None:
        if self._usrpsSynced.isSet():
            return

        if self.synchronisationValid():
            self._usrpsSynced.set()
            return

        for _ in range(System.syncAttempts):
            self.__setTimeToZeroNextPps()
            if self.synchronisationValid():
                self._usrpsSynced.set()
                return
            self.sleep(System.timeBetweenSyncAttempts)
        raise RuntimeError(f"Tried at least {self.syncAttempts} syncing wihout succes.")

    def synchronisationValid(self) -> bool:
        """Returns true if synchronisation of the USRPs is valid."""
        currentFpgaTimes = self.__getCurrentFpgaTimes()
        return (
            np.max(currentFpgaTimes) - np.min(currentFpgaTimes)
            < System.syncThresholdSec
        )

    def __setTimeToZeroNextPps(self) -> None:
        for usrp in self.__usrpClients.keys():
            self.__usrpClients[usrp].client.setTimeToZeroNextPps()
            logging.info("Set time to zero for PPS.")
        self.sleep(1.1)

    def sleep(self, delay: float) -> None:
        """Let's the system sleep for `delay` seconds."""
        time.sleep(delay)

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
            key: item.client.collect() for key, item in self.__usrpClients.items()
        }
        self.__assertNoClippedValues(samples)
        return samples

    def getSupportedSamplingRates(self, usrpName: str) -> np.ndarray:
        """Returns supported sampling rates.

        Args:
            usrpName (str): Identifier of USRP to be queried.

        Returns:
            np.ndarray: Array of supported sampling rates.
        """
        return self.__usrpClients[usrpName].client.getSupportedSamplingRates()

    def __assertNoClippedValues(self, samples: Dict[str, List[MimoSignal]]) -> None:
        for usrpName, usrpConfigSamples in samples.items():
            if any(
                containsClippedValue(mimoSignal) for mimoSignal in usrpConfigSamples
            ):
                raise ValueError(
                    f"USRP {usrpName} contains clipped values. Please check your gains."
                )
