import unittest
from unittest.mock import Mock
import sys
import os

sys.path.extend([os.path.join("build", "lib"), os.path.join("release_build", "lib")])

import numpy as np
import numpy.testing as npt

from server.rpc_server import (
    UsrpServer,
    serializeComplexArray,
    deserializeComplexArray,
)
from usrp_pybinding import Usrp, TxStreamingConfig, RxStreamingConfig, RfConfig


class TestSerializationComplexArr(unittest.TestCase):
    def test_oneDimensionalArray_complexValues(self) -> None:
        oneDimensionalArr = np.ones(3, dtype=np.complex64)
        real, imag = serializeComplexArray(oneDimensionalArr)

        self.assertListEqual(imag, np.imag(oneDimensionalArr).tolist())
        self.assertListEqual(real, np.real(oneDimensionalArr).tolist())

    def test_nonComplexArrayYieldsZeroImaginary(self) -> None:
        arr = np.ones(3)
        real, imag = serializeComplexArray(arr)

        self.assertListEqual(imag, np.imag(arr).tolist())
        self.assertListEqual(real, np.real(arr).tolist())

    def test_ndArrayShouldNotBeSupported(self) -> None:
        arr = np.ones((2, 3))
        self.assertRaises(ValueError, lambda: serializeComplexArray(arr))


class TestDeserializationComplexArr(unittest.TestCase):
    def test_properDeserialization(self) -> None:
        imagList = [1, 2, 3]
        realList = [4, 5, 6]

        expectedArr = np.array(realList) + 1j * np.array(imagList)
        deserializedArr = deserializeComplexArray((realList, imagList))
        npt.assert_array_almost_equal(deserializedArr, expectedArr)

    def test_noImagSamples_mismatch_noRealSamples(self) -> None:
        imagList = [0]
        realList = [1, 2]

        self.assertRaises(
            ValueError, lambda: deserializeComplexArray((realList, imagList))
        )


class TestUsrpServer(unittest.TestCase):
    def test_configureTxCalledWithCorrectArguments(self) -> None:
        TIME_OFFSET = 2.0
        REAL_LIST = [2, 3]
        IMAG_LIST = [0, 1]

        usrpMock = Mock()
        usrpServer = UsrpServer(usrpMock)
        usrpServer.configureTx(
            sendTimeOffset=TIME_OFFSET,
            samples=[(REAL_LIST, IMAG_LIST)],
        )

        self.assertAlmostEqual(
            usrpMock.setTxConfig.call_args[0][0].sendTimeOffset, TIME_OFFSET
        )
        np.testing.assert_array_almost_equal(
            usrpMock.setTxConfig.call_args[0][0].samples[0],
            np.array(REAL_LIST) + 1j * np.array(IMAG_LIST),
        )

    def test_configureRxCAlledWithCorrectArguments(self) -> None:
        NO_SAMPLES = int(1e3)
        TIME_OFFSET = 2.0

        usrpMock = Mock()
        usrpServer = UsrpServer(usrpMock)
        usrpServer.configureRx(receiveTimeOffset=TIME_OFFSET, noSamples=NO_SAMPLES)

        self.assertAlmostEqual(
            usrpMock.setRxConfig.call_args[0][0].receiveTimeOffset, TIME_OFFSET
        )
        self.assertAlmostEqual(
            usrpMock.setRxConfig.call_args[0][0].noSamples, NO_SAMPLES
        )
