import unittest
import numpy as np
import numpy.testing as nt

import uhd_wrapper.usrp_pybinding as binding


class TestTxStreamingConfig(unittest.TestCase):
    def test_canConstruct(self) -> None:
        binding.TxStreamingConfig()
        binding.TxStreamingConfig([np.array([5])], 8)

    def test_holdsCorrectValuesAfterConstruction(self) -> None:
        dut = binding.TxStreamingConfig([np.array([5, 9])], 8)
        nt.assert_array_equal(dut.samples, [np.array([5, 9])])
        self.assertIs(type(dut.samples), list)
        self.assertEqual(dut.sendTimeOffset, 8)

    def test_canSetFieldsAfterConstruction(self) -> None:
        signals = [np.array([8, 3]), np.array([9, 7])]
        dut = binding.TxStreamingConfig()
        dut.samples = signals
        dut.sendTimeOffset = 42

        self.assertEqual(dut.sendTimeOffset, 42)
        nt.assert_array_equal(dut.samples, signals)

    def test_inCppConstructedVersionMatchesLocallyConstructedVersion(self) -> None:
        signals = [np.array([8, 3]), np.array([9, 7])]
        dut = binding.TxStreamingConfig(signals, 5)
        self.assertEqual(dut, binding._createTxConfig(signals, 5))


class TestRxStreamingConfig(unittest.TestCase):
    def test_construction(self) -> None:
        binding.RxStreamingConfig()
        binding.RxStreamingConfig(receiveTimeOffset=5, noSamples=42)

    def test_holdsCorrectValues(self) -> None:
        dut = binding.RxStreamingConfig(receiveTimeOffset=5, noSamples=42)
        self.assertEqual(dut.receiveTimeOffset, 5)
        self.assertEqual(dut.noSamples, 42)

    def test_canSetFieldsAfterConstruction(self) -> None:
        dut = binding.RxStreamingConfig()
        dut.receiveTimeOffset = 5
        dut.noSamples = 42

        self.assertEqual(dut.receiveTimeOffset, 5)
        self.assertEqual(dut.noSamples, 42)


class TestMimoSignal(unittest.TestCase):
    def test_conversionFromCpp(self) -> None:
        res = binding._returnVectorOfMimoSignals()  # returns hard-coded values from C++

        self.assertIs(type(res), list)
        self.assertEqual(len(res), 1)
        self.assertIs(type(res[0]), list)
        self.assertEqual(len(res[0]), 2)
        self.assertIs(type(res[0][0]), np.ndarray)
        self.assertIs(type(res[0][1]), np.ndarray)
        nt.assert_array_equal(res[0][0], np.array([1, 2, 3, 4]))
        nt.assert_array_equal(res[0][1], np.array([5, 6, 7, 8]))
