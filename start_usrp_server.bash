export XDG_CONFIG_HOME=/home/root/
export HOME=/home/root/
cd /home/root/usrp_uhd_api/
. env/bin/activate
echo "$(date +%d.%m.%Y:%H:%M:%S): Started USRP server." >> usrp_server_log.txt
python start_usrp_server.py &>>usrp_sever_log.txt
echo "$(date +%d.%m.%Y:%H:%M:%S): Stopped USRP server." >> usrp_server_log.txt
