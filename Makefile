service: rpc-server.service
	cp $< /etc/systemd/system/$<
	systemctl enable $<
	systemctl start $<
