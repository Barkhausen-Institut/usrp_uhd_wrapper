import time

import uhd_wrapper.usrp_pybinding as pybinding


class RestartingUsrp(pybinding.Usrp):
    @staticmethod
    def create(ip: str, masterClockRate: float = 0, 
               desiredDeviceType: str = "x410") -> 'RestartingUsrp':
        RestartTrials = 5
        SleepTime = 5

        for _ in range(RestartTrials):
            try:
                result = RestartingUsrp(ip, masterClockRate)
            except RuntimeError:
                print(f"Creating of USRP failed... Retrying after {SleepTime} seconds.")
                time.sleep(SleepTime)
                continue

            if result.deviceType.upper() != desiredDeviceType.upper():
                raise RuntimeError(
                    f"""Current USRP is {result.deviceType},
                    you requested to start on {desiredDeviceType}."""
                )
            return result
        raise RuntimeError("Could not start USRP... exiting.")
