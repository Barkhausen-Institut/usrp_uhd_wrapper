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


class TestFakeUsrp(unittest.TestCase):
    def test_construction(self) -> None:
        binding.FakeUsrp()

    def test_txConfig(self) -> None:
        txConfig = binding.TxStreamingConfig(samples=[np.array([8]), np.array([9])],
                                             sendTimeOffset=8)

        dut = binding.FakeUsrp()
        dut.setTxConfig(txConfig)

        self.assertEqual(dut.lastTxConfig, txConfig)

    def test_rxConfig(self) -> None:
        rxConfig = binding.RxStreamingConfig(noSamples=9, receiveTimeOffset=8)

        dut = binding.FakeUsrp()
        dut.setRxConfig(rxConfig)

        self.assertEqual(dut.lastRxConfig, rxConfig)

    def test_collectCorrectValues(self) -> None:
        dut = binding.FakeUsrp()
        # return dummy values hard-coded in C++. This test is here to
        # verify if the data is correctly transferred between C++ and
        # python.
        res = dut.collect()
        self.assertIs(type(res), list)
        self.assertEqual(len(res), 1)
        self.assertIs(type(res[0]), list)
        self.assertEqual(len(res[0]), 2)
        self.assertIs(type(res[0][0]), np.ndarray)
        self.assertIs(type(res[0][1]), np.ndarray)
        nt.assert_array_equal(res[0][0], np.array([1, 2, 3, 4]))
        nt.assert_array_equal(res[0][1], np.array([5, 6, 7, 8]))
