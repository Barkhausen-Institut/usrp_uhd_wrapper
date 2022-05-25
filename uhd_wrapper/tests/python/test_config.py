import unittest

from uhd_wrapper.utils.config import MimoSignal, containsClippedValue

import numpy as np


class TestMimoSignal(unittest.TestCase):
    def setUp(self) -> None:
        self.mimoSignal = MimoSignal(
            signals=[np.zeros(10, dtype=np.complex64), np.zeros(10, dtype=np.complex64)]
        )

    def test_oneSignalContainsPositiveClippedRealValue(self) -> None:
        self.mimoSignal.signals[0][0] = 1.0 + 0.5j
        self.assertTrue(containsClippedValue(self.mimoSignal))

    def test_oneSignalContainsNegativeClippedImagValue(self) -> None:
        self.mimoSignal.signals[0][0] = 0.0 + -1.5j
        self.assertTrue(containsClippedValue(self.mimoSignal))

    def test_noSignalContainsClippedValue(self) -> None:
        self.assertFalse(containsClippedValue(self.mimoSignal))
