import time
from datetime import datetime

import feedparser
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
    'title': '',
    'state': 'stop',
    'volume': '',
    'elapsed': 0,
    'duration': 0,  # Prevent division by zero
}

# Define Podcast List
podcasts = [
    {
        'name': 'Marketplace',
        'feed_url': 'https://www.marketplace.org/feed/podcast/marketplace/'
    },
    {
        'name': 'Wait Wait...',
        'feed_url': 'https://feeds.npr.org/344098539/podcast.xml'
    },
    {
        'name': 'No Stupid ?s',
        'feed_url': 'https://feeds.simplecast.com/dfh_verV'

    },
    {
        'name': 'Freakanomics',
        'feed_url': 'https://feeds.simplecast.com/Y8lFbOT4'
    }

    # Add more podcasts as needed
]

# Define functions
def get_latest_episode(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        if feed.entries:
            for entry in feed.entries:
                if entry.enclosures and 'audio' in entry.enclosures[0]['type']:
                    episode_url = entry.enclosures[0]['url']
                    episode_title = entry.title
                    return episode_url, episode_title
            # If no entries with audio enclosures are found
            return None, None
        else:
            # No entries in the feed
            return None, None
    except Exception as e:
        print(f"Error fetching feed: {e}")
        return None, None

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
        status["state"] = "load"
        while player.get_state() != vlc.State.Playing:
            time.sleep(.1)  # Allow VLC to start
            update_display()
        status["state"] = "play"
        status['duration'] = player.get_length() / 1000  # Duration in seconds
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

def draw_play_symbol(draw, x, y, size):
    # Coordinates for the triangle
    points = [
        (x, y),  # Top point
        (x, y + size),  # Bottom point
        (x + size, y + size / 2)  # Right point
    ]
    draw.polygon(points, outline=255, fill=255)

def draw_pause_symbol(draw, x, y, width, height):
    # Left rectangle
    draw.rectangle((x, y, x + width, y + height), outline=255, fill=255)
    # Right rectangle
    draw.rectangle((x + width + 2, y, x + 2 * width + 2, y + height), outline=255, fill=255)

def draw_stop_symbol(draw, x, y, size):
    draw.rectangle((x, y, x + size, y + size), outline=255, fill=255)


def draw_eject_symbol(draw, x, y, width, height):
    # Draw the triangle (upward-pointing)
    triangle_height = height * 0.6  # Proportion of total height
    triangle_points = [
        (x + width / 2, y),  # Top center point
        (x, y + triangle_height),  # Bottom left
        (x + width, y + triangle_height)  # Bottom right
    ]
    draw.polygon(triangle_points, outline=255, fill=255)

    # Draw the rectangle (base)
    base_y = y + triangle_height + 2  # Slight gap between triangle and base
    base_height = height * 0.2
    draw.rectangle(
        (x, base_y, x + width, base_y + base_height),
        outline=255,
        fill=255
    )

# Global variables to keep track of scrolling state
scroll_x = 0  # Current scroll position
scroll_reset = False  # Flag to reset scroll position
title_font = ImageFont.truetype("DejaVuSansMono.ttf", size=12)  # Load the font once

def update_display():
    global scroll_x, scroll_reset, status
    with canvas(oled) as draw:
        font = title_font

        # Draw podcast name
        draw.text((0, 0), f"{status['name']}", font=font, fill=255)

        # Draw playback symbol
        symbol_x = WIDTH - 20
        symbol_y = 0
        if status['state'] == 'play':
            draw_play_symbol(draw, symbol_x, symbol_y, size=10)
        elif status['state'] == 'pause':
            draw_pause_symbol(draw, symbol_x, symbol_y, width=5, height=10)
        elif status['state'] == 'stop':
            draw_stop_symbol(draw, symbol_x, symbol_y, size=10)
        elif status['state'] == 'load':
            draw_eject_symbol(draw, symbol_x, symbol_y, width=10, height=10)

        # Draw podcast episode title with scrolling
        title_text = status['title']
        title_width = font.getlength(title_text)  # Use font.getsize() instead
        max_text_width = WIDTH - 2  # Available width for the text
        if title_width > max_text_width:
            # Title is too long, scrolling needed
            if scroll_reset:
                # Reset scroll position after a full scroll
                scroll_x = max_text_width
                scroll_reset = False

            draw.text((2 - scroll_x, 12), title_text, font=font, fill=255)
            scroll_x += 4  # Adjust scroll speed by changing the increment
            if scroll_x >= title_width + 4:  # Extra pixels to provide a gap
                scroll_reset = True
        else:
            # Title fits on the screen, no scrolling needed
            draw.text((0, 12), title_text, font=font, fill=255)
            scroll_x = 0  # Reset scroll position
            scroll_reset = False

        # Draw progress bar
        progress_bar_length = WIDTH - 30
        elapsed = status['elapsed']
        duration = status['duration']
        progress = int((elapsed / duration) * progress_bar_length) if duration > 0 else 0

        draw.rectangle((2, 26, WIDTH - 30, 34), outline=255, fill=0)
        draw.rectangle((2, 26, 2 + progress, 34), outline=255, fill=255)

        # Draw volume
        draw.text((WIDTH - 20, 24), f"{status['volume']}%", font=font, fill=255)

        # Draw elapsed and total time
        elapsed_str = time.strftime('%M:%S', time.gmtime(elapsed))
        duration_str = time.strftime('%M:%S', time.gmtime(duration))
        draw.text((0, 36), f"{elapsed_str} / {duration_str}", font=font, fill=255)

        # Draw current time
        draw.text((WIDTH-35, 52), datetime.now().strftime('%H:%M'), font=font, fill=255)


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
            status['state'] = "pause" if is_paused else "play"
    else:
        if event == RotaryEncoder.CLOCKWISE:
            current_podcast_index = (current_podcast_index + 1) % len(podcasts)
            status['name'] = podcasts[current_podcast_index]['name']
            print("ENC1_CW")
        elif event == RotaryEncoder.ANTICLOCKWISE:
            current_podcast_index = (current_podcast_index - 1) % len(podcasts)
            status['name'] = podcasts[current_podcast_index]['name']
            print("ENC1_CCW")
        elif event == RotaryEncoder.BUTTONDOWN:
            print("ENC1_BTN")
            # Start playback
            podcast = podcasts[current_podcast_index]
            episode_url, episode_title = get_latest_episode(podcast['feed_url'])
            print(episode_url)
            if episode_url:
                status['name'] = podcast['name']
                status['title'] = episode_title
                #status['state'] = "Loading..."
                update_display()
                play_podcast(episode_url)
                status['state'] = "play"
            else:
                status['state'] = "stop"
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
status['state'] = "stop"
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
                        status['state'] = "stop"
        update_display()
        time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    stop_podcast()
    GPIO.cleanup()
    #oled.clear()
