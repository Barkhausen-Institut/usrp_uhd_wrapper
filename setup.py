from setuptools import setup

setup(
    name="usrp_uhd_api",
    version="0.0.0",
    packages=["usrp_client"],
    python_requires=">=3.9",
    install_requires=[
        "zerorpc~=0.6.3",
        "pyzmq~=22.3.0",
        "numpy~=1.21.6",
    ],
)
