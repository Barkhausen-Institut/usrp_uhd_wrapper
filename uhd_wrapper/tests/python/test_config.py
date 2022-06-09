import unittest

from uhd_wrapper.utils.config import (
    MimoSignal,
    rxContainsClippedValue,
    txContainsClippedValue,
)

import numpy as np


class TestMimoSignal(unittest.TestCase):
    def setUp(self) -> None:
        self.mimoSignal = MimoSignal(
            signals=[np.zeros(10, dtype=np.complex64), np.zeros(10, dtype=np.complex64)]
        )

    def test_oneRxSignalContainsPositiveClippedRealValue(self) -> None:
        self.mimoSignal.signals[0][0] = 1.0 + 0.5j
        self.assertTrue(rxContainsClippedValue(self.mimoSignal))

    def test_oneRxSignalContainsNegativeClippedImagValue(self) -> None:
        self.mimoSignal.signals[0][0] = 0.0 + -1.5j
        self.assertTrue(rxContainsClippedValue(self.mimoSignal))

    def test_noRxSignalContainsClippedValue(self) -> None:
        self.assertFalse(rxContainsClippedValue(self.mimoSignal))

    def test_oneTxSignalContainsExactValueOfOne(self) -> None:
        self.mimoSignal.signals[0][0] = 1.0 + 0.5j
        self.assertFalse(txContainsClippedValue(self.mimoSignal))

    def test_oneTxSignalContainsPositiveClippedRealValue(self) -> None:
        self.mimoSignal.signals[0][0] = 1.5 + 0.5j
        self.assertTrue(txContainsClippedValue(self.mimoSignal))

    def test_oneTxSignalContainsNegativeClippedImagValue(self) -> None:
        self.mimoSignal.signals[0][0] = 0.0 + -1.5j
        self.assertTrue(txContainsClippedValue(self.mimoSignal))

    def test_noTxSignalContainsClippedValue(self) -> None:
        self.assertFalse(txContainsClippedValue(self.mimoSignal))
