from typing import List
import numpy as np

import zerorpc

from uhd_wrapper.utils.config import (
    RxStreamingConfig,
    TxStreamingConfig,
    RfConfig,
    MimoSignal,
)


class _RpcClient:
    def __init__(self, ip: str, port: int = 5555) -> None:
        """Initializes the UsrpClient.

        Args:
            ip (str): The IP where the RPC Server is running
            port (int): The port where the RPC Server is running
        """
        self.__ip = ip
        self.__port = port
        self.__rpcClient = self._createClient(ip, port)

    @property
    def ip(self) -> str:
        return self.__ip

    @property
    def port(self) -> int:
        return self.__port

    def _createClient(self, ip: str, port: int) -> zerorpc.Client:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)

            # throws after 1second timeout. Succeeds, if USRP can be reached.
            s.connect((ip, port))
            s.close()
        except socket.timeout:
            raise IOError(f"Usrp {ip}:{port} not reachable")

        result = zerorpc.Client(heartbeat=10)
        result.connect(f"tcp://{ip}:{port}")
        return result

    def configureRx(self, rxConfig: RxStreamingConfig) -> None:
        """Call `configureRx` on server and serialize `rxConfig`.

        Args:
            rxConfig (RxStreamingConfig): Streaming config.
        """
        self.__rpcClient.configureRx(rxConfig.receiveTimeOffset,
                                     rxConfig.numSamples,
                                     rxConfig.antennaPort,
                                     rxConfig.numRepetitions,
                                     rxConfig.repetitionPeriod)

    def configureTx(self, txConfig: TxStreamingConfig) -> None:
        """Call `configureTx` on server and serialize `txConfig`."""
        self.__rpcClient.configureTx(
            txConfig.sendTimeOffset,
            txConfig.samples.serialize(),
            txConfig.numRepetitions
        )

    def execute(self, baseTime: float) -> None:
        """Execute the current configuration at the receiver side.

        Set the baseTime on the receiver to the desired value.

        Args:
            baseTime (float): FPGA time all streaming config time offsets refer to.
        """
        self.__rpcClient.execute(baseTime)

    def executeImmediately(self) -> None:
        """Execute the current TX and RX streaming configs immediately, without
        synchronizing the stream time with other USRPs in the setup.

        """
        self.__rpcClient.execute(-1)

    def collect(self) -> List[MimoSignal]:
        """Collect samples from RPC server and deserialize them.

        Returns:
            List[MimoSignal]:
                Each list item corresponds to the samples of one streaming configuration.
        """
        return [MimoSignal.deserialize(c) for c in self.__rpcClient.collect()]

    def configureRfConfig(self, rfConfig: RfConfig) -> None:
        """Serialize `rfConfig` and request configuration on RPC server."""
        self.__rpcClient.configureRfConfig(rfConfig.serialize())

    def setTimeToZeroNextPps(self) -> None:
        """Sets the time to zero on the next PPS edge."""
        self.__rpcClient.setTimeToZeroNextPps()

    def getCurrentFpgaTime(self) -> int:
        """Queries current FPGA time from RPC server."""
        return self.__rpcClient.getCurrentFpgaTime()

    def getCurrentSystemTime(self) -> int:
        """Queries current system time from RPC server."""
        return self.__rpcClient.getCurrentSystemTime()

    def getRfConfig(self) -> RfConfig:
        """Queries RfConfig from RPC server and deserializes it."""
        return RfConfig.deserialize(self.__rpcClient.getRfConfig())

    def getMasterClockRate(self) -> float:
        """Queries the master clock rate of the USRP."""
        return self.__rpcClient.getMasterClockRate()

    def getSupportedSampleRates(self) -> List[float]:
        """Queries the samples rates supported by the device."""
        return self.__rpcClient.getSupportedSampleRates()

    def resetStreamingConfigs(self) -> None:
        """Tells USRP to reset streaming configs."""
        self.__rpcClient.resetStreamingConfigs()

    def setSyncSource(self, syncSource: str) -> None:
        """Set synchronization source. See
        https://files.ettus.com/manual/classuhd_1_1rfnoc_1_1mb__controller.html#a76d77388ad2142c4d05297c8d14131d2
        for details.

        Args:
            syncSource (str): Use "internal" or "external".

        """
        self.__rpcClient.setSyncSource(syncSource)

    def getNumAntennas(self) -> int:
        """Return the number of available TX and RX antennas of the device"""
        return self.__rpcClient.getNumAntennas()

    def getRemoteVersion(self) -> str:
        """Return the Python package version of the remotely running UsrpServer
        """
        return self.__rpcClient.getVersion()

    def getLocalVersion(self) -> str:
        import usrp_client
        return usrp_client.__version__


class UsrpClient(_RpcClient):
    """This class is the interface to the UsrpServer running on the USRP device

    Under the hood, we communicate with the UsrpServer class which wraps zerorpc. ZeroRPC
    implements remote procedure call client-server architecture using zeromq as a communication
    protocol. `UsrpClient` forwards user calls to the RPC server and serializes them if
    required.
    """

    @staticmethod
    def create(ip: str, port: int = 5555) -> 'UsrpClient':
        """Create a USRP client which is connected to the
        UsrpServer running at given ip and port"""

        return UsrpClient(ip, port)

    def __init__(self, ip: str, port: int) -> None:
        """Private constructor. Should not be called. Use UsrpClient.create
        """

        super().__init__(ip, port)
        self.resetStreamingConfigs()
        self._rfConfiguredOnce = False

    def configureRfConfig(self, rfConfig: RfConfig) -> None:
        self._rfConfiguredOnce = True
        return super().configureRfConfig(rfConfig)

    def execute(self, baseTime: float) -> None:
        if not self._rfConfiguredOnce:
            raise RuntimeError("RF has not been configured "
                               "for the USRP device before execution!")
        super().execute(baseTime)

    def getSupportedSamplingRates(self) -> np.ndarray:
        """Queries USRP for the supported sampling rates.

        Deprecated! Use `getSupportedSampleRates` instead.
        """
        return np.array(self.getSupportedSampleRates())
