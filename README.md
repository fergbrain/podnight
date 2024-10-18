# PodNight

# License

The MIT License (MIT)

Copyright (c) 2024 Andrew Ferguson for Fergcorp, LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


# Warning

This is crap code intended as a proof of concept

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

# Turn of LEDS
## Pi
Edit `/boot/firmware/config.txt` to add:
```ini
# Turn of LEDs
dtparam=pwr_led_trigger=default-on
dtparam=pwr_led_activelow=on
dtparam=act_led_trigger=none
dtparam=act_led_activelow=off
```

## WiFi Dongle

Create/edit `/etc/rc.local` to add:

```bash
#!/bin/sh -e
echo 0 | tee /sys/class/leds/rt2800usb-phy*::assoc/brightness
exit 0
```
