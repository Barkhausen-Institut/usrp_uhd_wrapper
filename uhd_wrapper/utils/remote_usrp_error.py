class AnnotatedUsrpException(Exception):
    def __init__(self, actualUsrpMsg: str, usrpName: str = "") -> None:
        self.actualUsrpMsg = actualUsrpMsg
        self.usrpName = usrpName

        self.msg = self.__createExceptionMsg()
        super().__init__(self.msg)

    def __createExceptionMsg(self) -> str:
        return f"Usrp {self.usrpName}: {self.actualUsrpMsg}"
