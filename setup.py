from setuptools import setup, find_packages  # type: ignore
import os


VERSION = "0.0.0"
NAME = "usrp_uhd_api"

lsb = os.popen("lsb_release -a").read()

runningOnUsrp = "Description:\tAlchemy" in lsb
if runningOnUsrp:
    print("Setting up for USRP Development")
    setup(
        name=NAME,
        version=VERSION,
        packages=["uhd_wrapper"],
        python_requires=">=3.7",
        install_requires=[
            line.strip() for line in open("requirements_usrp.txt").readlines()
        ],
    )

else:
    print("Setting up for host development")
    setup(
        name=NAME,
        version=VERSION,
        packages=find_packages(exclude=["examples"]),
        python_requires=">=3.9",
        install_requires=[
            "zerorpc~=0.6.3",
            "pyzmq~=22.3.0",
            "numpy~=1.21.6",
            "matplotlib~=3.5.2",
            "dataclasses-json~=0.5.7",
        ],
    )
