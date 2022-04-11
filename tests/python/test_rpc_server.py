from multiprocessing.sharedctypes import Value
import unittest

import numpy as np
import numpy.testing as npt

from rpcserver.rpc_server import serializeComplexArray, deserializeComplexArray


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

        self.assertRaises(ValueError, lambda: deserializeComplexArray((realList, imagList)))
