from setuptools import setup, find_packages  # type: ignore
import os


VERSION = "1.7.0"
AUTHOR = "Maximilian Matthé"
AUTHOR_EMAIL = "maximilian.matthe@barkhauseninstitut.org"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

lsb = os.popen("lsb_release -a").read()

runningOnUsrp = "Description:\tAlchemy" in lsb
if runningOnUsrp:
    print("Setting up for USRP Development")
    setup(
        name="usrp-uhd-server",
        version=VERSION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        packages=["uhd_wrapper"],
        python_requires=">=3.7",
        install_requires=[
            line.strip() for line in open("requirements_usrp.txt").readlines()
        ],
    )

else:
    print("Setting up for host development")
    setup(
        name="usrp-uhd-client",
        version=VERSION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        description="Universal Software Defined Radio Hardware Driver Remote Client",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/Barkhausen-Institut/usrp_uhd_wrapper",
        project_urls={
            "Documentation": "https://barkhausen-institut.github.io/usrp_uhd_wrapper",
            "Barkhausen Institute": "https://www.barkhauseninstitut.org",
            "Bug Tracker": "https://github.com/Barkhausen-Institut/usrp_uhd_wrapper/issues",
        },
        classifiers=[
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "License :: OSI Approved :: GNU Affero General Public License v3",
            "Operating System :: OS Independent",
            "Development Status :: 2 - Pre-Alpha",
            "Natural Language :: English",
            "Topic :: Scientific/Engineering",
        ],
        packages=find_packages(exclude=["examples"]),
        python_requires=">=3.9",
        install_requires=[
            "zerorpc~=0.6.3",
            "pyzmq~=25.1.1",
            "numpy>=1.23.5",
            "matplotlib>=3.6.2",
            "dataclasses-json~=0.5.7",
        ],
    )
