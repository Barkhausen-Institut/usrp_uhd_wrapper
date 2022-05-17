from typing import List
import numpy as np

import zerorpc

from uhd_wrapper.utils.config import (
    RxStreamingConfig,
    TxStreamingConfig,
    RfConfig,
    MimoSignal,
)


class UsrpClient:
    """This class is the RPC client to the RPC server running on the USRP

    Under the hood, we communicate with the UsrpServer class which wraps zerorpc. ZeroRPC
    implements remote procedure call client-server architecture using zeromq as a communication
    protocol. `UsrpClient` forwards user calls to the RPC server and serializes them if
    required.
    """

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

    def getSupportedDecimationRatios(self) -> np.ndarray:
        """Returns the supported decimation ratios."""
        decimationRatios = np.append(np.array([1]), np.arange(start=2, stop=57, step=2))
        return decimationRatios

    def getSupportedSamplingRates(self) -> np.ndarray:
        """Queries USRP for the supported sampling rates."""
        return self.getMasterClockRate() / self.getSupportedDecimationRatios()

    def resetStreamingConfigs(self) -> None:
        """Tells USRP to reset streaming configs."""
        self.__rpcClient.resetStreamingConfigs()
