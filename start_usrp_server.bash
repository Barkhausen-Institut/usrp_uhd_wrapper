export XDG_CONFIG_HOME=/home/root/
export HOME=/home/root/
export UHD_LOG_FILE=usrp_uhd_log.txt
cd /home/root/usrp_uhd_api/
. env/bin/activate
python start_usrp_server.py
