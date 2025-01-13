# Music and Video Downloader

This is a Python-based tool designed to help you download music, videos, subtitles, and playlists from YouTube and other platforms supported by ‍`yt-dlp‍`. It offers advanced features such as parallel downloading of multiple files and the ability to set metadata for audio files, ensuring a seamless and organized downloading experience.
---

## Features

- Download music in the best quality and convert to various formats (MP3, M4A, WAV, AAC, FLAC, OGG)
- Download videos with selectable quality (1080p, 720p, 480p, etc.)
- Download subtitles for videos
- Download all tracks from a playlist
- Parallel downloading of multiple files simultaneously
- Automatic metadata setting for audio files
- Proxy support for downloading
---

## Requirements

- Python 3.x
- `yt-dlp`
- `ffmpeg`
---

## Installation

1. First, ensure that Python 3.x is installed on your system.
2. Then, install the required libraries using the following command:

   ```bash
   pip install yt-dlp mutagen tqdm
   ```
3. If `ffmpeg` is not installed on your system, the script will automatically install it (only for Linux systems).
---

## Usage
- Run the script using the following command:
    ```bash
    python Downloader.py
    ```
- After running, an interactive menu will be displayed, prompting you to choose the type of download (music, video, subtitles, playlist, or parallel download). Then, enter the desired URL and other settings (such as output format, quality, and save path).
---

## Examples
- Download a music track:
    ```bash
    Enter the music URL: https://www.youtube.com/watch?v=example
    Enter output format (mp3/m4a/wav/aac/flac/ogg) [Default: mp3]: mp3
    Enter output directory [Default: current directory]: ./music
    ```
- Download a video:
    ```bash
    Enter the video URL: https://www.youtube.com/watch?v=example
    Enter output format (mp4/mkv) [Default: mp4]: mp4
    Enter video quality (e.g., 1080, 720, 480) [Default: best]: 1080
    Enter output directory [Default: current directory]: ./videos
    ```
- Download a playlist:
    ```bash
    Enter the playlist URL: https://www.youtube.com/playlist?list=example
    Enter output format (mp3/m4a/wav/aac/flac/ogg) [Default: mp3]: mp3
    Enter output directory [Default: current directory]: ./playlist
    ```
- Parallel download of multiple music tracks:
    ```bash
    Enter the music URLs (separated by space): https://www.youtube.com/watch?v=example1 https://www.youtube.com/watch?v=example2
    Enter output format (mp3/m4a/wav/aac/flac/ogg) [Default: mp3]: mp3
    Enter output directory [Default: current directory]: ./parallel_downloads
    ```
---

## Configuration
- You can save your default settings in the `config.json` file. This file is automatically created and can include settings such as the default output format, save path, and proxy.
---

## Limitations
- This script has only been tested on Linux, Windows, and macOS.
- Automatic installation of `ffmpeg` is only supported for Linux systems. For other systems, you need to install `ffmpeg` manually.
---

## 📞 Contact

For questions, feedback, or bug reports, contact the maintainer:
- **Email**: MrAmirRezaie70@gmail.com
- **Telegram**: [@MrAmirRezaie](https://t.me/MrAmirRezaie)
- **GitHub**: [internetScraper](https://github.com/MrAmirRezaie/internetScraper)
---

## License
- This project is released under the MIT License.
---

Happy Downloading! 😃