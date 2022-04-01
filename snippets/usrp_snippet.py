import sys
sys.path.extend(["release_build/lib/", "debug_build/lib/", "build/lib/"])
import pymod

ip = "localhost"
usrp = pymod.createUsrp(ip)