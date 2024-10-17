import time
import feedparser
from datetime import datetime
import RPi.GPIO as GPIO
import subprocess

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont

from pirotary.rotary_class import RotaryEncoder

# Initialize I2C interface and SH1106 OLED display
serial = i2c(port=1, address=0x3C)
oled = sh1106(serial)
oled.contrast(50)

WIDTH = oled.width
HEIGHT = oled.height

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Initialize variables
current_podcast_index = 0
volume = 50  # Initial volume level
is_playing = False
player_process = None

# Initialize Status
status={
    'name':  '',
    'state': '',
    'volume': '',
}


# Initialize Rotary Encoder 1 (Podcast Selection with Push Button)
def rotary_encoder1_event(event):
    global current_podcast_index, is_playing, player_process, status
    if event == RotaryEncoder.CLOCKWISE:
         current_podcast_index = (current_podcast_index + 1) % len(podcasts)
         status['name']=podcasts[current_podcast_index]['name']
    elif event == RotaryEncoder.ANTICLOCKWISE:
        current_podcast_index = (current_podcast_index - 1) % len(podcasts)
        status['name']=podcasts[current_podcast_index]['name']
    elif event == RotaryEncoder.BUTTONDOWN:
        if not is_playing:
            # Start playback
            podcast = podcasts[current_podcast_index]
            episode_url = get_latest_episode(podcast['feed_url'])
            if episode_url:
                player_process = play_podcast(episode_url)
                is_playing = True
                status['state']="Playing" # update_display(podcast['name'], "Playing", volume)
            else:
                status['state']="No Episode" #[#update_display(podcast['name'], "No Episode", volume)
        else:
            # Pause playback
            player_process.terminate()
            is_playing = False
            status['state']="Paused" #update_display(podcasts[current_podcast_index]['name'], "Paused", volume)

# Initialize rotary encoder
encoder1 = RotaryEncoder(
    pinA=23,
    pinB=24,
    button=17,
    callback=rotary_encoder1_event
)

# Initialize Rotary Encoder 2 (Volume Control with Push Button)
def rotary_encoder2_event(event):
    global volume
    if event == RotaryEncoder.CLOCKWISE:
        volume = min(100, volume + 5)
    elif event == RotaryEncoder.ANTICLOCKWISE:
        volume = max(0, volume - 5)
    '''elif event == RotaryEncoder.BUTTONDOWN:
        # Implement functionality for encoder 2 button press
        print("Encoder 2 button pressed")
        # For example, stop playback entirely
        global is_playing, player_process
        if is_playing:
            player_process.terminate()
            is_playing = False
            update_display(podcasts[current_podcast_index]['name'], "Stopped", volume)
    '''
    subprocess.call(['amixer', 'set', 'PCM', f'{volume}%'])


encoder2 = RotaryEncoder(
    pinA=14,
    pinB=15,
    button=4,
    callback=rotary_encoder2_event
)


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


# Define functions
def get_latest_episode(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        if feed.entries:
            for entry in feed.entries:
                if entry.enclosures and 'audio' in entry.enclosures[0]['type']:
                    return entry.enclosures[0]['url']
        return None
    except Exception as e:
        print(f"Error fetching feed: {e}")
        return None

def play_podcast(url):
    process = subprocess.Popen(['mpg123', url])
    return process


def update_display(podcast_name, playback_status, volume):
    with canvas(oled) as draw:
        font = ImageFont.load_default()
        # Draw podcast name
        draw.text((0, 0), f"Podcast: {podcast_name}", font=font, fill=255)
        # Draw playback status
        draw.text((0, 16), f"Status: {playback_status}", font=font, fill=255)
        # Draw volume
        draw.text((0, 32), f"Volume: {volume}%", font=font, fill=255)
        # Draw current time
        draw.text((0, 48), datetime.now().strftime('%H:%M:%S'), font=font, fill=255)


# Main loop
try:
    update_display(podcasts[current_podcast_index]['name'], "Stopped", volume)
    while True:
        # Check if playback has finished
        if is_playing and player_process.poll() is not None:
            # Playback finished
            is_playing = False
            update_display(podcasts[current_podcast_index]['name'], "Finished", volume)
        else:
            update_display(status['name'], status['state'], volume)
        time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
    oled.clear()
