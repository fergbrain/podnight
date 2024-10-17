import time
import feedparser
from datetime import datetime
import RPi.GPIO as GPIO
import vlc  # Use VLC for media playback
import threading

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont, ImageDraw

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
volume = 50  # Initial volume level (0-100)
is_playing = False
is_paused = False
player = None
player_lock = threading.Lock()

# Initialize Status
status = {
    'name': '',
    'state': '',
    'volume': '',
    'elapsed': 0,
    'duration': 1,  # Prevent division by zero
}

# Define Podcast List
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
    global player, is_playing, is_paused, status
    with player_lock:
        if player:
            player.stop()
        instance = vlc.Instance('--input-repeat=-1')
        player = instance.media_player_new()
        media = instance.media_new(url)
        player.set_media(media)
        player.audio_set_volume(volume)
        player.play()
        time.sleep(1)  # Allow VLC to start
        status['duration'] = player.get_length() / 1000  # Duration in seconds
        print("Duration")
        print(status['duration'])
        is_playing = True
        is_paused = False

def pause_podcast():
    global player, is_paused
    with player_lock:
        if player:
            player.pause()
            is_paused = not is_paused  # Toggle pause state

def stop_podcast():
    global player, is_playing, is_paused
    with player_lock:
        if player:
            player.stop()
            player.release()
            player = None
        is_playing = False
        is_paused = False
        status['elapsed'] = 0

def seek_podcast(seconds):
    global player
    with player_lock:
        if player:
            current_time = player.get_time()
            new_time = current_time + (seconds * 1000)  # VLC uses milliseconds
            player.set_time(int(new_time))

def update_display():
    with canvas(oled) as draw:
        font = ImageFont.load_default()
        # Draw podcast name
        draw.text((0, 0), f"{status['name']}", font=font, fill=255)
        # Draw playback status
        draw.text((0, 12), f"Status: {status['state']}", font=font, fill=255)
        # Draw volume
        draw.text((0, 24), f"Volume: {status['volume']}%", font=font, fill=255)
        # Draw progress bar
        progress_bar_length = WIDTH - 4
        elapsed = status['elapsed']
        duration = status['duration']
        progress = int((elapsed / duration) * progress_bar_length) if duration > 0 else 0
        draw.rectangle((2, 36, WIDTH - 2, 44), outline=255, fill=0)
        draw.rectangle((2, 36, 2 + progress, 44), outline=255, fill=255)
        # Draw elapsed and remaining time
        elapsed_str = time.strftime('%M:%S', time.gmtime(elapsed))
        remaining = max(0, duration - elapsed)
        remaining_str = time.strftime('%M:%S', time.gmtime(remaining))
        draw.text((0, 48), f"{elapsed_str} / {remaining_str}", font=font, fill=255)

# Initialize Rotary Encoder 1 (Podcast Selection with Push Button)
def rotary_encoder1_event(event):
    global current_podcast_index, is_playing, status, is_paused
    if is_playing:
        if event == RotaryEncoder.CLOCKWISE:
            seek_podcast(30)  # Skip forward 30 seconds
        elif event == RotaryEncoder.ANTICLOCKWISE:
            seek_podcast(-30)  # Skip backward 30 seconds
        elif event == RotaryEncoder.BUTTONDOWN:
            pause_podcast()
            status['state'] = "Paused" if is_paused else "Playing"
    else:
        if event == RotaryEncoder.CLOCKWISE:
            current_podcast_index = (current_podcast_index + 1) % len(podcasts)
            status['name'] = podcasts[current_podcast_index]['name']
        elif event == RotaryEncoder.ANTICLOCKWISE:
            current_podcast_index = (current_podcast_index - 1) % len(podcasts)
            status['name'] = podcasts[current_podcast_index]['name']
        elif event == RotaryEncoder.BUTTONDOWN:
            # Start playback
            podcast = podcasts[current_podcast_index]
            episode_url = get_latest_episode(podcast['feed_url'])
            if episode_url:
                status['name'] = podcast['name']
                status['state'] = "Loading..."
                update_display()
                play_podcast(episode_url)
                status['state'] = "Playing"
            else:
                status['state'] = "No Episode"
    update_display()

encoder1 = RotaryEncoder(
    pinA=23,
    pinB=24,
    button=17,
    callback=rotary_encoder1_event
)

# Initialize Rotary Encoder 2 (Volume Control with Push Button)
def rotary_encoder2_event(event):
    global volume, status
    if event == RotaryEncoder.CLOCKWISE:
        volume = min(100, volume + 5)
    elif event == RotaryEncoder.ANTICLOCKWISE:
        volume = max(0, volume - 5)
    elif event == RotaryEncoder.BUTTONDOWN:
        # Mute or unmute
        if volume > 0:
            volume = 0
        else:
            volume = 50  # Restore to a default volume
    status['volume'] = volume
    if player:
        player.audio_set_volume(volume)
    update_display()

encoder2 = RotaryEncoder(
    pinA=14,
    pinB=15,
    button=4,
    callback=rotary_encoder2_event
)

# Initialize status display
status['name'] = podcasts[current_podcast_index]['name']
status['state'] = "Stopped"
status['volume'] = volume
update_display()

# Main loop
try:
    while True:
        if is_playing and not is_paused:
            # Update elapsed time
            with player_lock:
                if player:
                    status['elapsed'] = player.get_time() / 1000  # Convert to seconds
                    if player.get_state() == vlc.State.Ended:
                        # Playback finished
                        stop_podcast()
                        status['state'] = "Finished"
        update_display()
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    stop_podcast()
    GPIO.cleanup()
    oled.clear()
