from typing import Tuple, List
import sys
import os

sys.path.extend([os.path.join("build", "lib"), os.path.join("release_build", "lib")])
import numpy as np

from usrp_pybinding import Usrp, TxStreamingConfig, RxStreamingConfig, RfConfig


def serializeComplexArray(data: np.ndarray) -> Tuple[List, List]:
    data = np.squeeze(data)
    if len(data.shape) == 2:
        raise ValueError("Array must be one dimensional!")
    return (np.real(data).tolist(), np.imag(data).tolist())


def deserializeComplexArray(data: Tuple[List, List]) -> np.ndarray:
    if len(data[0]) != len(data[1]):
        raise ValueError(
            """Number of imaginary samples
                            mismatches number of real samples."""
        )
    arr = np.array(data[0]) + 1j * np.array(data[1])
    return arr


class UsrpServer:
    def __init__(self, usrp: Usrp) -> None:
        self.__usrp = usrp

    def configureTx(
        self, sendTimeOffset: float, samples: List[Tuple[List, List]]
    ) -> None:
        self.__usrp.setTxConfig(
            TxStreamingConfig(
                samples=[deserializeComplexArray(frame) for frame in samples],
                sendTimeOffset=sendTimeOffset,
            )
        )

    def configureRx(self, receiveTimeOffset: float, noSamples: int) -> None:
        self.__usrp.setRxConfig(
            RxStreamingConfig(noSamples=noSamples, receiveTimeOffset=receiveTimeOffset)
        )
