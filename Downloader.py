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

# Configuration file to store user preferences
CONFIG_FILE = "config.json"


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
        print("Package manager not detected. Please install ffmpeg manually.")
        sys.exit(1)

    print(f"Detected package manager: {package_manager}")
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
        print("ffmpeg installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing ffmpeg: {e}")
        print("Please install ffmpeg manually: https://ffmpeg.org/download.html")
        sys.exit(1)


def install_requirements():
    """Install yt-dlp and ffmpeg automatically."""
    try:
        import yt_dlp
    except ImportError:
        print("Installing yt-dlp...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
        except subprocess.CalledProcessError as e:
            print(f"Error installing yt-dlp: {e}")
            sys.exit(1)

    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ffmpeg not found. Installing ffmpeg...")
        if platform.system().lower() == "linux":
            install_ffmpeg()
        else:
            print("Unsupported operating system. Please install ffmpeg manually.")
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
        print(f"Error setting metadata: {e}")


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
                print(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                print(f"Download error: {e}")
                return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
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
                print(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                print(f"Download error: {e}")
                return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
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
                print(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                print(f"Download error: {e}")
                return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
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
                print(f"Attempt {attempt + 1} failed. Retrying...")
            else:
                print(f"Download error: {e}")
                return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None


def download_parallel(urls, proxy=None, output_format="mp3", output_dir=".", retries=3):
    """Download multiple files in parallel."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for url in urls:
            futures.append(executor.submit(download_music, url, proxy, output_format, output_dir, retries))
        for future in futures:
            future.result()


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
    print("6. Exit")
    choice = input("Enter your choice (1/2/3/4/5/6): ")
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
            print("Exiting...")
            sys.exit(0)

        else:
            print("Invalid choice. Please try again.")