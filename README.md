# PodNight

PodNight is a Raspberry Pi-based podcast player that allows you to listen to your favorite podcasts before bed -- helping keep your phone out of the bedroom.

It features two rotary encoders for navigation and volume control, and an OLED display that shows the current podcast episode information. This guide will walk you through how to set up your own PodNight device using a Raspberry Pi Model 2 B, two KY-040 rotary encoders, and a 1.3” OLED display.

## Warning

* This is crap code intended as a proof of concept.
* I used ChatGPT to help write code and documention. There may be errors.

## Features 
* Listen to the latest episode of predefined podcasts. 
* Control playback and volume with rotary encoders.
* Automatically fetch the latest podcast episodes using feedparser. 
* OLED display to show the current episode, volume, and playback state. 
* Automatic scrolling of long episode titles on the OLED display. 
* Play, pause, and skip forward/backward functionality. 
* Mute control using the rotary encoder. 
* Python-based and set up to run as a systemd service on Raspberry Pi.

## Hardware Requirements
Note: affiliate links are below

* Raspberry Pi Model 2 B (or compatible)
* Two KY-040 rotary encoders
* * Such as: [5pcs 360 Degree Rotary Encoder Module KY-040 Brick Sensor Development Board with Push Button](https://amzn.to/3UeKLFA)
* 1.3” OLED display (I2C, SH1106 driver)
* * Such as: [MakerFocus 2pcs OLED Display Module I2C 128X64 1.3 Inch Display Module SSD1106 White](https://amzn.to/3NxPpL4)
* USB WiFi adapter (if required)
* Speaker or headphones for audio output
* * Such as: [Philmore Pillow Speaker w/ 6' Cord ](https://amzn.to/3UebSR5)
* Power supply for the Raspberry Pi
* SD card with Raspberry Pi OS installed

## Pinout Information

Below is the pinout information for wiring the Raspberry Pi Model 2 B to the 1.3" OLED display (I2C) and the two KY-040 rotary encoders. Ensure you double-check connections before powering on your Raspberry Pi to avoid damaging any components.

### **OLED Display (I2C, SH1106) Wiring**
The OLED display uses the I2C protocol for communication. Connect the display's pins as follows:

| OLED Pin  | Raspberry Pi Pin | GPIO Number | Description |
|-----------|------------------|-------------|-------------|
| VCC       | Pin 2 (5V)       | N/A         | Power (5)   |
| GND       | Pin 20 (GND)     | N/A         | Ground      |
| SCL       | Pin 5 (GPIO 3)   | GPIO 3 (SCL) | I2C Clock   |
| SDA       | Pin 3 (GPIO 2)   | GPIO 2 (SDA) | I2C Data    |

### **KY-040 Rotary Encoders Wiring**
Each KY-040 rotary encoder has five pins: **CLK**, **DT**, **SW** (button), **+** (power), and **GND**.

#### **Rotary Encoder 1 (Podcast Selection & Playback Control)**

| Encoder Pin | Raspberry Pi Pin | GPIO Number | Description        |
|-------------|------------------|-------------|--------------------|
| CLK         | Pin 16           | GPIO 23     | Clock signal       |
| DT          | Pin 18           | GPIO 24     | Data signal        |
| SW          | Pin 11           | GPIO 17     | Push button switch |
| +           | Pin 17 (3.3V)    | N/A         | Power (3.3V)       |
| GND         | Pin 14 (GND)     | N/A         | Ground             |

#### **Rotary Encoder 2 (Volume Control)**

| Encoder Pin | Raspberry Pi Pin | GPIO Number | Description        |
|-------------|-----------------|-------------|--------------------|
| CLK         | Pin 8           | GPIO 14     | Clock signal       |
| DT          | Pin 10          | GPIO 15     | Data signal        |
| SW          | Pin 7           | GPIO 4      | Push button switch |
| +           | Pin 1 (3.3V)    | N/A         | Power (3.3V)       |
| GND         | Pin 9 (GND)     | N/A         | Ground             |


If you use a different model of Raspberry Pi, double-check the GPIO pinout as some models may have different pin mappings.



## Software Requirements

* Python 3

The following Python libraries:
* RPi.GPIO
* feedparser
* vlc
* luma.oled
* Pillow (PIL)

You can install the required Python libraries using pip:
```bash
pip3 install RPi.GPIO feedparser python-vlc luma.oled pillow
```

## Controlling the Device

### Left Rotary Encoder:
* Rotate to navigate through the list of available podcasts.
* Press to play/pause the current episode.
* Rotate while playing to skip forward/backward by 30 seconds.
### Right Rotary Encoder:
* Rotate to adjust the volume.
* Press to mute/unmute the audio.


## Customizing Podcast Feeds

To customize which podcasts are available, modify the podcasts array in the podcast_player.py file:
```python
podcasts = [
    {
        'name': 'Marketplace',
        'feed_url': 'https://www.marketplace.org/feed/podcast/marketplace/'
    },
    {
        'name': 'Podcast Two',
        'feed_url': 'https://example.com/podcast2/feed'
    },
    # Add more podcasts as needed
]
```

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