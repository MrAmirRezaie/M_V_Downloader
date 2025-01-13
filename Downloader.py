import os
import platform
import subprocess
import sys
import yt_dlp
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from tqdm import tqdm
import threading
import json
from concurrent.futures import ThreadPoolExecutor
import time
from datetime import datetime
import logging
from pathlib import Path
import re

# Configuration file to store user preferences
CONFIG_FILE = "config.json"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def detect_package_manager():
    """Detect the package manager used by the Linux distribution."""
    package_managers = {
        "apt": "apt",  # Debian/Ubuntu
        "yum": "yum",  # RHEL/CentOS
        "dnf": "dnf",  # Fedora
        "pacman": "pacman",  # Arch
        "zypper": "zypper",  # openSUSE
    }
    for cmd, pkg_manager in package_managers.items():
        if subprocess.run(["which", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            return pkg_manager
    return None

def install_ffmpeg():
    """Install ffmpeg using the detected package manager."""
    package_manager = detect_package_manager()
    if not package_manager:
        logging.error("Package manager not detected. Please install ffmpeg manually.")
        sys.exit(1)

    logging.info(f"Detected package manager: {package_manager}")
    try:
        if package_manager == "apt":
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], check=True)
        elif package_manager == "yum":
            subprocess.run(["sudo", "yum", "install", "-y", "ffmpeg"], check=True)
        elif package_manager == "dnf":
            subprocess.run(["sudo", "dnf", "install", "-y", "ffmpeg"], check=True)
        elif package_manager == "pacman":
            subprocess.run(["sudo", "pacman", "-Sy", "--noconfirm", "ffmpeg"], check=True)
        elif package_manager == "zypper":
            subprocess.run(["sudo", "zypper", "install", "-y", "ffmpeg"], check=True)
        logging.info("ffmpeg installed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error installing ffmpeg: {e}")
        logging.error("Please install ffmpeg manually: https://ffmpeg.org/download.html")
        sys.exit(1)

def install_requirements():
    """Install yt-dlp and ffmpeg automatically."""
    try:
        import yt_dlp
    except ImportError:
        logging.info("Installing yt-dlp...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing yt-dlp: {e}")
            sys.exit(1)

    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        logging.info("ffmpeg not found. Installing ffmpeg...")
        if platform.system().lower() == "linux":
            install_ffmpeg()
        else:
            logging.error("Unsupported operating system. Please install ffmpeg manually.")
            sys.exit(1)

def set_metadata(file_path, metadata):
    """Set metadata for the downloaded file."""
    try:
        audio = EasyID3(file_path)
        audio['title'] = metadata.get('title', 'Unknown Title')
        audio['artist'] = metadata.get('artist', 'Unknown Artist')
        audio['album'] = metadata.get('album', 'Unknown Album')
        audio.save()
    except Exception as e:
        logging.error(f"Error setting metadata: {e}")

def download_music(url, proxy=None, output_format="mp3", output_dir=".", retries=3):
    """Download music in the best quality and save in the specified format."""
    ydl_opts = {
        'format': 'bestaudio/best',  # Best audio quality
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': output_format,  # Output format
            'preferredquality': '320',  # Best audio quality
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),  # Output file name
        'quiet': False,  # Show download progress
        'no_warnings': False,  # Show warnings
        'proxy': proxy,  # Proxy settings
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                file_path = file_path.replace(".webm", f".{output_format}").replace(".m4a", f".{output_format}")

                # Set metadata
                metadata = {
                    'title': info_dict.get('title', 'Unknown Title'),
                    'artist': info_dict.get('artist', 'Unknown Artist'),
                    'album': info_dict.get('album', 'Unknown Album'),
                }
                set_metadata(file_path, metadata)

                return os.path.abspath(file_path)  # Return absolute path of the downloaded file
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def download_video(url, proxy=None, output_format="mp4", output_dir=".", quality="best", retries=3):
    """Download video in the specified quality and format."""
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',  # Best video quality
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),  # Output file name
        'quiet': False,  # Show download progress
        'no_warnings': False,  # Show warnings
        'proxy': proxy,  # Proxy settings
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                return os.path.abspath(file_path)  # Return absolute path of the downloaded file
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def download_subtitles(url, proxy=None, output_dir=".", retries=3):
    """Download subtitles for the video."""
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'srt',  # Subtitle format
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),  # Output file name
        'quiet': False,  # Show download progress
        'no_warnings': False,  # Show warnings
        'proxy': proxy,  # Proxy settings
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                return os.path.abspath(file_path)  # Return absolute path of the downloaded subtitles
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def download_playlist(url, proxy=None, output_format="mp3", output_dir=".", retries=3):
    """Download all tracks from a playlist."""
    ydl_opts = {
        'format': 'bestaudio/best',  # Best audio quality
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': output_format,  # Output format
            'preferredquality': '320',  # Best audio quality
        }],
        'outtmpl': os.path.join(output_dir, '%(playlist_index)s - %(title)s.%(ext)s'),  # Output file name
        'quiet': False,  # Show download progress
        'no_warnings': False,  # Show warnings
        'proxy': proxy,  # Proxy settings
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                return os.path.abspath(output_dir)  # Return absolute path of the downloaded playlist
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def download_parallel(urls, proxy=None, output_format="mp3", output_dir=".", retries=3):
    """Download multiple files in parallel."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for url in urls:
            futures.append(executor.submit(download_music, url, proxy, output_format, output_dir, retries))
        for future in futures:
            future.result()

def download_video_with_subs(url, proxy=None, output_format="mp4", output_dir=".", quality="best", retries=3):
    """Download video with embedded subtitles."""
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'srt',
        'embedsubs': True,  # Embed subtitles in the video
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'proxy': proxy,
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                return os.path.abspath(file_path)
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def download_audio_from_video(url, proxy=None, output_format="mp3", output_dir=".", retries=3):
    """Download audio from a video."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': output_format,
            'preferredquality': '320',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'proxy': proxy,
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                file_path = file_path.replace(".webm", f".{output_format}").replace(".m4a", f".{output_format}")
                return os.path.abspath(file_path)
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def download_video_custom_quality(url, proxy=None, output_format="mp4", output_dir=".", quality="best", retries=3):
    """Download video with custom quality."""
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'proxy': proxy,
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                return os.path.abspath(file_path)
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def download_video_chunked(url, proxy=None, output_format="mp4", output_dir=".", quality="best", retries=3):
    """Download video in chunks."""
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'proxy': proxy,
        'continuedl': True,  # Continue partially downloaded files
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                return os.path.abspath(file_path)
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def download_with_speed_limit(url, proxy=None, output_format="mp3", output_dir=".", speed_limit="1M", retries=3):
    """Download with a speed limit."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': output_format,
            'preferredquality': '320',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'proxy': proxy,
        'ratelimit': speed_limit,  # Limit download speed (e.g., "1M" for 1 MB/s)
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                file_path = file_path.replace(".webm", f".{output_format}").replace(".m4a", f".{output_format}")
                return os.path.abspath(file_path)
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def download_video_advanced(url, proxy=None, output_format="mp4", output_dir=".", quality="best", codec="h264",
                            framerate=30, retries=3):
    """Download video with advanced settings."""
    ydl_opts = {
        'format': f'bestvideo[height<={quality}][vcodec^={codec}][fps<={framerate}]+bestaudio/best[height<={quality}]',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'proxy': proxy,
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                return os.path.abspath(file_path)
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def download_subtitles_multilang(url, proxy=None, output_dir=".", languages=["en"], retries=3):
    """Download subtitles in multiple languages."""
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'srt',
        'subtitleslangs': languages,  # List of languages (e.g., ["en", "fr", "es"])
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'proxy': proxy,
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                return os.path.abspath(file_path)
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def scheduled_download(url, proxy=None, output_format="mp4", output_dir=".", quality="best", scheduled_time=None):
    """Schedule a download for a specific time."""
    if scheduled_time:
        scheduled_time = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M:%S")
        while datetime.now() < scheduled_time:
            time.sleep(1)
        logging.info("Starting scheduled download...")
        return download_video(url, proxy, output_format, output_dir, quality)
    else:
        logging.info("No scheduled time provided. Downloading now...")
        return download_video(url, proxy, output_format, output_dir, quality)

def download_preview(url, proxy=None, output_dir=".", duration=10):
    """Download a preview of the video."""
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(output_dir, '%(title)s_preview.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'proxy': proxy,
        'postprocessor_args': ['-t', str(duration)],  # Duration of the preview in seconds
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            return os.path.abspath(file_path)
    except yt_dlp.utils.DownloadError as e:
        logging.error(f"Download error: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

def download_compressed_video(url, proxy=None, output_format="mp4", output_dir=".", quality="best",
                              compression_level=23, retries=3):
    """Download video with compression."""
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        'outtmpl': os.path.join(output_dir, '%(title)s_compressed.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'proxy': proxy,
        'postprocessor_args': ['-crf', str(compression_level)],  # Compression level (0-51, lower is better quality)
    }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                return os.path.abspath(file_path)
        except yt_dlp.utils.DownloadError as e:
            if attempt < retries - 1:
                logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                logging.error(f"Download error: {e}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

def load_config():
    """Load user preferences from the configuration file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save user preferences to the configuration file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def interactive_menu():
    """Display an interactive menu for the user."""
    print("Welcome to the Music and Video Downloader!")
    print("1. Download a single track")
    print("2. Download a playlist")
    print("3. Download a video")
    print("4. Download subtitles")
    print("5. Download multiple tracks in parallel")
    print("6. Download video with embedded subtitles")
    print("7. Download audio from video")
    print("8. Download video with custom quality")
    print("9. Download video in chunks")
    print("10. Download with speed limit")
    print("11. Download video with advanced settings")
    print("12. Download subtitles in multiple languages")
    print("13. Schedule a download")
    print("14. Download a preview of the video")
    print("15. Download compressed video")
    print("16. Exit")
    choice = input("Enter your choice (1-16): ")
    return choice

if __name__ == "__main__":
    # Install requirements
    install_requirements()

    # Load user preferences
    config = load_config()

    # Interactive menu
    while True:
        choice = interactive_menu()

        if choice == "1":
            # Get the music URL from the user
            music_url = input("Enter the music URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp3/m4a/wav/aac/flac/ogg) [Default: mp3]: ").lower() or "mp3"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the music
            try:
                downloaded_file_path = download_music(music_url, proxy, output_format, output_dir)
                if downloaded_file_path:
                    print(f"Music downloaded successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download the music.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "2":
            # Get the playlist URL from the user
            playlist_url = input("Enter the playlist URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp3/m4a/wav/aac/flac/ogg) [Default: mp3]: ").lower() or "mp3"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the playlist
            try:
                downloaded_playlist_path = download_playlist(playlist_url, proxy, output_format, output_dir)
                if downloaded_playlist_path:
                    print(f"Playlist downloaded successfully! Files saved at: {downloaded_playlist_path}")
                else:
                    print("Failed to download the playlist.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "3":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp4/mkv) [Default: mp4]: ").lower() or "mp4"

            # Get quality from the user
            quality = input("Enter video quality (e.g., 1080, 720, 480) [Default: best]: ") or "best"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the video
            try:
                downloaded_file_path = download_video(video_url, proxy, output_format, output_dir, quality)
                if downloaded_file_path:
                    print(f"Video downloaded successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download the video.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "4":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the subtitles
            try:
                downloaded_file_path = download_subtitles(video_url, proxy, output_dir)
                if downloaded_file_path:
                    print(f"Subtitles downloaded successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download subtitles.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "5":
            # Get the music URLs from the user
            music_urls = input("Enter the music URLs (separated by space): ").split()

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp3/m4a/wav/aac/flac/ogg) [Default: mp3]: ").lower() or "mp3"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the music in parallel
            try:
                download_parallel(music_urls, proxy, output_format, output_dir)
                print("Music downloaded successfully!")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "6":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp4/mkv) [Default: mp4]: ").lower() or "mp4"

            # Get quality from the user
            quality = input("Enter video quality (e.g., 1080, 720, 480) [Default: best]: ") or "best"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the video with embedded subtitles
            try:
                downloaded_file_path = download_video_with_subs(video_url, proxy, output_format, output_dir, quality)
                if downloaded_file_path:
                    print(f"Video with embedded subtitles downloaded successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download the video with embedded subtitles.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "7":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp3/m4a/wav/aac/flac/ogg) [Default: mp3]: ").lower() or "mp3"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the audio from the video
            try:
                downloaded_file_path = download_audio_from_video(video_url, proxy, output_format, output_dir)
                if downloaded_file_path:
                    print(f"Audio from video downloaded successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download the audio from video.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "8":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp4/mkv) [Default: mp4]: ").lower() or "mp4"

            # Get quality from the user
            quality = input("Enter video quality (e.g., 1080, 720, 480) [Default: best]: ") or "best"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the video with custom quality
            try:
                downloaded_file_path = download_video_custom_quality(video_url, proxy, output_format, output_dir,
                                                                     quality)
                if downloaded_file_path:
                    print(f"Video with custom quality downloaded successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download the video with custom quality.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "9":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp4/mkv) [Default: mp4]: ").lower() or "mp4"

            # Get quality from the user
            quality = input("Enter video quality (e.g., 1080, 720, 480) [Default: best]: ") or "best"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the video in chunks
            try:
                downloaded_file_path = download_video_chunked(video_url, proxy, output_format, output_dir, quality)
                if downloaded_file_path:
                    print(f"Video downloaded in chunks successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download the video in chunks.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "10":
            # Get the music URL from the user
            music_url = input("Enter the music URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp3/m4a/wav/aac/flac/ogg) [Default: mp3]: ").lower() or "mp3"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Get speed limit from the user
            speed_limit = input("Enter speed limit (e.g., 1M for 1 MB/s) [Default: 1M]: ") or "1M"

            # Download with speed limit
            try:
                downloaded_file_path = download_with_speed_limit(music_url, proxy, output_format, output_dir,
                                                                 speed_limit)
                if downloaded_file_path:
                    print(f"Music downloaded with speed limit successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download the music with speed limit.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "11":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp4/mkv) [Default: mp4]: ").lower() or "mp4"

            # Get quality from the user
            quality = input("Enter video quality (e.g., 1080, 720, 480) [Default: best]: ") or "best"

            # Get codec from the user
            codec = input("Enter video codec (e.g., h264, vp9) [Default: h264]: ") or "h264"

            # Get framerate from the user
            framerate = input("Enter video framerate (e.g., 30, 60) [Default: 30]: ") or "30"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the video with advanced settings
            try:
                downloaded_file_path = download_video_advanced(video_url, proxy, output_format, output_dir, quality,
                                                               codec, framerate)
                if downloaded_file_path:
                    print(f"Video with advanced settings downloaded successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download the video with advanced settings.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "12":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Get languages from the user
            languages = input("Enter languages for subtitles (e.g., en,fr,es) [Default: en]: ").split(",") or ["en"]

            # Download subtitles in multiple languages
            try:
                downloaded_file_path = download_subtitles_multilang(video_url, proxy, output_dir, languages)
                if downloaded_file_path:
                    print(f"Subtitles in multiple languages downloaded successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download subtitles in multiple languages.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "13":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp4/mkv) [Default: mp4]: ").lower() or "mp4"

            # Get quality from the user
            quality = input("Enter video quality (e.g., 1080, 720, 480) [Default: best]: ") or "best"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Get scheduled time from the user
            scheduled_time = input("Enter scheduled time (YYYY-MM-DD HH:MM:SS) [Leave blank for immediate download]: ")

            # Schedule the download
            try:
                downloaded_file_path = scheduled_download(video_url, proxy, output_format, output_dir, quality,
                                                          scheduled_time)
                if downloaded_file_path:
                    print(f"Video scheduled download completed successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to schedule the download.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "14":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Get preview duration from the user
            duration = input("Enter preview duration in seconds (e.g., 10) [Default: 10]: ") or "10"

            # Download the preview
            try:
                downloaded_file_path = download_preview(video_url, proxy, output_dir, int(duration))
                if downloaded_file_path:
                    print(f"Video preview downloaded successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download the video preview.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "15":
            # Get the video URL from the user
            video_url = input("Enter the video URL: ")

            # Get proxy settings from the user (optional)
            proxy = input(
                "Enter proxy (e.g., http://user:pass@host:port or socks5://user:pass@host:port) [Leave blank if not using proxy]: ")

            # Get output format from the user
            output_format = input("Enter output format (mp4/mkv) [Default: mp4]: ").lower() or "mp4"

            # Get quality from the user
            quality = input("Enter video quality (e.g., 1080, 720, 480) [Default: best]: ") or "best"

            # Get compression level from the user
            compression_level = input("Enter compression level (0-51, lower is better quality) [Default: 23]: ") or "23"

            # Get output directory from the user
            output_dir = input("Enter output directory [Default: current directory]: ") or "."

            # Download the compressed video
            try:
                downloaded_file_path = download_compressed_video(video_url, proxy, output_format, output_dir, quality,
                                                                 int(compression_level))
                if downloaded_file_path:
                    print(f"Compressed video downloaded successfully! File path: {downloaded_file_path}")
                else:
                    print("Failed to download the compressed video.")
            except KeyboardInterrupt:
                print("\nDownload canceled by the user.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == "16":
            print("Exiting...")
            sys.exit(0)

        else:
            print("Invalid choice. Please try again.")
