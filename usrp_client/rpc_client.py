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

    def __init__(self, rpcClient: zerorpc.Client) -> None:
        """Initializes the UsrpClient.

        Args:
            rpcClient (zerorpc.Client): zerorpc.Client that is already connected to RPC server.
        """
        self.__rpcClient = rpcClient

    def configureRx(self, rxConfig: RxStreamingConfig) -> None:
        """Call `configureRx` on server and serialize `rxConfig`.

        Args:
            rxConfig (RxStreamingConfig): Streaming config.
        """
        self.__rpcClient.configureRx(rxConfig.receiveTimeOffset, rxConfig.noSamples)

    def configureTx(self, txConfig: TxStreamingConfig) -> None:
        """Call `configureTx` on server and serialize `txConfig`."""
        self.__rpcClient.configureTx(
            txConfig.sendTimeOffset,
            txConfig.samples.serialize(),
        )

    def execute(self, baseTime: float) -> None:
        """Execute the current configuration at the receiver side.

        Set the baseTime on the receiver to the desired value.

        Args:
            baseTime (float): FPGA time all streaming config time offsets refer to.
        """
        self.__rpcClient.execute(baseTime)

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

    def resetStreamingConfigs(self) -> None:
        """Tells USRP to reset streaming configs."""
        self.__rpcClient.resetStreamingConfigs()


class UsrpClient(_RpcClient):
    """This class is the interface to the UsrpServer running on the USRP device

    Under the hood, we communicate with the UsrpServer class which wraps zerorpc. ZeroRPC
    implements remote procedure call client-server architecture using zeromq as a communication
    protocol. `UsrpClient` forwards user calls to the RPC server and serializes them if
    required.
    """

    @staticmethod
    def create(ip: str, port: int) -> 'UsrpClient':
        """Create a USRP client which is connected to the
        UsrpServer running at given ip and port"""

        rpc = zerorpc.Client()
        rpc.connect(f"tcp://{ip}:{port}")
        return UsrpClient(rpc)

    def __init__(self, rpcClient: zerorpc.Client) -> None:
        """Private constructor. Should not be called. Use UsrpClient.create
        """

        super().__init__(rpcClient)
        self._rfConfiguredOnce = False

    def configureRfConfig(self, rfConfig: RfConfig) -> None:
        self._rfConfiguredOnce = True
        return super().configureRfConfig(rfConfig)

    def execute(self, baseTime: float) -> None:
        if not self._rfConfiguredOnce:
            raise RuntimeError("RF has not been configured "
                               "for the USRP device before execution!")
        super().execute(baseTime)

    def getSupportedDecimationRatios(self) -> np.ndarray:
        """Returns the supported decimation ratios."""
        decimationRatios = np.append(np.array([1]), np.arange(start=2, stop=57, step=2))
        return decimationRatios

    def getSupportedSamplingRates(self) -> np.ndarray:
        """Queries USRP for the supported sampling rates."""
        return self.getMasterClockRate() / self.getSupportedDecimationRatios()
