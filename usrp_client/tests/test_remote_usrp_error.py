import unittest

from usrp_client.remote_usrp_error import RemoteUsrpError, MultipleErrors


class TestRemoteUsrpError(unittest.TestCase):
    def test_standardExceptionContainsEmptyUsrpField(self) -> None:
        error = RemoteUsrpError("foo")
        self.assertEqual(error.usrpName, "")

    def test_msgCreatedWithUsrpName(self) -> None:
        usrpName = "usrp1"
        error = RemoteUsrpError("foo", usrpName)
        self.assertIn(usrpName, str(error))


class TestMultipleErrors(unittest.TestCase):
    def test_oneError(self) -> None:
        errorMsg = "foo"
        e = RuntimeError(errorMsg)
        multipleE = MultipleErrors([e])
        self.assertIn(errorMsg, str(multipleE))

    def test_multipleErrors(self) -> None:
        errorMsg1 = "foo"
        errorMsg2 = "bar"

        e1 = RuntimeError(errorMsg1)
        e2 = RuntimeError(errorMsg2)

        multipleE = MultipleErrors([e1, e2])
        self.assertIn(errorMsg1, str(multipleE))
        self.assertIn(errorMsg2, str(multipleE))
