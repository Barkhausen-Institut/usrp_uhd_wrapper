import unittest

from usrp_client.errors import RemoteUsrpError, MultipleRemoteUsrpErrors


class TestRemoteUsrpError(unittest.TestCase):
    def test_standardExceptionContainsEmptyUsrpField(self) -> None:
        error = RemoteUsrpError("foo")
        self.assertEqual(error.usrpName, "")

    def test_msgCreatedWithUsrpName(self) -> None:
        usrpName = "usrp1"
        error = RemoteUsrpError("foo", usrpName)
        self.assertIn(usrpName, str(error))


class TestMultipleUsrpErrors(unittest.TestCase):
    def test_oneError(self) -> None:
        errorMsg = "foo"
        e = RemoteUsrpError(errorMsg)
        multipleE = MultipleRemoteUsrpErrors([e])
        self.assertIn(errorMsg, str(multipleE))

    def test_multipleErrors(self) -> None:
        errorMsg1 = "foo"
        errorMsg2 = "bar"

        e1 = RemoteUsrpError(errorMsg1)
        e2 = RemoteUsrpError(errorMsg2)

        multipleE = MultipleRemoteUsrpErrors([e1, e2])
        self.assertIn(errorMsg1, str(multipleE))
        self.assertIn(errorMsg2, str(multipleE))
