# Install as service

```sudo nano /etc/systemd/system/podcast_player.service```

```service
[Unit]
Description=Podcast Player Service
After=network.target sound.target

[Service]
Type=simple
User=andrewferguson
ExecStart=/home/andrewferguson/podnight/venv/bin/python /home/andrewferguson/podnight/podcast_player.py
WorkingDirectory=/home/andrewferguson/podnight
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

**Reload Systemd Configuration**

```sudo systemctl daemon-reload```

**Enable the service at boot**

```sudo systemctl enable podcast_player.service```

**Start the service**

```sudo systemctl start podcast_player.service```


**Verify the service status**

```sudo systemctl status podcast_player.service```

**View service logs**

```sudo journalctl -u podcast_player.service -f```