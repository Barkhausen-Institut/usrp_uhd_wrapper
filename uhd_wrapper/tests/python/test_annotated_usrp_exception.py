import unittest

from uhd_wrapper.utils.annotated_usrp_exception import AnnotatedUsrpException


def rethrowException_emptyUsrpField(msg: str) -> None:
    try:
        raise Exception(msg)
    except Exception as e:
        raise AnnotatedUsrpException(e)


def rethrowException_setUsrpField(msg: str, usrpName: str) -> None:
    try:
        raise Exception(msg)
    except Exception as e:
        raise AnnotatedUsrpException(e, usrpName)


class TestAnnotatedUsrpException(unittest.TestCase):
    def test_standardExceptionContainsEmptyUsrpField(self) -> None:
        try:
            rethrowException_emptyUsrpField("foo")
        except AnnotatedUsrpException as e:
            self.assertEqual(e.usrpName, "")

    def test_msgCreatedWithUsrpExceptionMsg(self) -> None:
        DUMMY_MSG = "foo"
        USRP_NAME = "usrp1"
        try:
            rethrowException_setUsrpField(DUMMY_MSG, USRP_NAME)
        except AnnotatedUsrpException as e:
            self.assertIn(USRP_NAME, str(e))

    def test_msgContainsMsgOfReraisedException(self) -> None:
        DUMMY_MSG = "foo"
        try:
            rethrowException_setUsrpField(DUMMY_MSG, "usrp1")
        except AnnotatedUsrpException as e:
            self.assertIn(DUMMY_MSG, str(e))
