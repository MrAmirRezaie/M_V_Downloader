# Music and Video Downloader

This is a Python script for downloading music, videos, subtitles, and playlists from YouTube and other platforms supported by `yt-dlp`. The script provides advanced features such as custom quality downloads, parallel downloads, default settings, and even speed-limited downloads.

## Features

- Download music in the best quality and convert to various formats (MP3, M4A, WAV, AAC, FLAC, OGG).
- Download videos with custom quality (1080p, 720p, 480p, etc.).
- Download subtitles separately or embedded in videos.
- Download entire playlists.
- Parallel downloading of multiple files simultaneously.
- Default settings for output directory, format, proxy, and quality.
- Extract audio from videos (video-less audio downloads).
- Download videos with advanced settings like codec and framerate.
- Download subtitles in multiple languages.
- Schedule downloads for a specific time.
- Download video previews.
- Download compressed videos.

## Prerequisites

- Python 3.x
- `yt-dlp`
- `ffmpeg` (for format conversion and audio extraction)

## Installation

1. Ensure Python 3.x is installed on your system. If not, download it from [here](https://www.python.org/downloads/).

2. Install the required libraries:

   ```bash
   pip install yt-dlp mutagen tqdm
   ```
3. Ensure `ffmpeg` is installed on your system. If not, download it from [here](https://ffmpeg.org/download.html) or use the script to install it automatically.

## Usage
- Run the script using the following command:
    ```bash
    python Downloader.py
    ```
- After running, an interactive menu will be displayed, prompting you to choose the type of download (music, video, subtitles, playlist, or parallel download). Then, enter the desired URL and other settings (such as output format, quality, and save path).
---

## Menu Options
1. Download a single track: Download a single music track with a specified format and quality.
2. Download a playlist: Download all tracks from a playlist.
3. Download a video: Download a video with specified quality and format.
4. Download subtitles: Download subtitles for a video.
5. Download multiple tracks in parallel: Download multiple music tracks simultaneously.
6. Download video with embedded subtitles: Download a video with embedded subtitles.
7. Download audio from video: Extract audio from a video and save it as an audio file.
8. Download video with custom quality: Download a video with custom quality settings.
9. Download video in chunks: Download a video in chunks for resuming interrupted downloads.
10. Download with speed limit: Download with a specified speed limit.
11. Download video with advanced settings: Download a video with advanced settings like codec and framerate.
12. Download subtitles in multiple languages: Download subtitles in multiple languages.
13. Schedule a download: Schedule a download for a specific time.
14. Download a video preview: Download a short preview of a video.
15. Download compressed video: Download a video with compression.
16. Exit: Exit the program.

## Default Settings
- You can save default settings such as the output directory, output format, proxy, and quality in the `config.json` file. This file is automatically created and stores your settings for future use.
---

## Limitations
- This script has only been tested on Linux, Windows, and macOS.
- Automatic installation of `ffmpeg` is only supported for Linux systems. For other systems, you need to install `ffmpeg` manually.
---

## 📞 Contact

For questions, feedback, or bug reports, contact the maintainer:
- **Email**: MrAmirRezaie70@gmail.com
- **Telegram**: [@MrAmirRezaie](https://t.me/MrAmirRezaie)
- **GitHub**: [MrAmirRezaie](https://github.com/MrAmirRezaie)
---

## Contributing
- Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.
---

## Support
- For any questions or support, please open an issue on the GitHub repository.
---

Enjoy downloading your media with ease! 🎶🎥
