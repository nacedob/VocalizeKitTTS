# VocalizeKitTTS 🎤→🎬

https://img.shields.io/badge/Python-3.8%252B-blue
https://img.shields.io/badge/License-MIT-green
https://img.shields.io/badge/Status-Beta-orange

Transform text into professional videos with natural voices, automatic subtitles, and background music. Convert EPUB, HTML, and text documents into engaging audiovisual content.

<p align="center"> <img src="https://img.shields.io/badge/Text_to_Speech-EdgeTTS-blueviolet" alt="TTS"> <img src="https://img.shields.io/badge/Subtitles-Vosk-ff69b4" alt="Subtitles"> <img src="https://img.shields.io/badge/Video-MoviePy-red" alt="Video"> </p>

## ✨ Features

- 🗣️ Natural Voices: Text-to-speech conversion using Microsoft Edge TTS (Spanish and English)

- 📝 Automatic Subtitles: SRT generation with precise timecodes using Vosk

- 📚 Multi-format Support: EPUB, HTML, and plain text processing

- 🎬 Video Creation: Combine audio, subtitles, images, and background music

- 🎚️ Full Control: Adjust speed, volume, subtitle styles, and more

- 📊 Colorful Logging: Process tracking with colors and timestamps

## 🚀 Quick Start
### Installation

```bash
#Clone the repository
git clone https://github.com/nacedob/VocalizeKitTTS.git
cd VocalizeKitTTS

# Install dependencies
pip install -r requirements.txt

# Download Vosk models (Spanish and English)
python download_models.py
``` 
### Basic Usage 
To see an example of a video generated with VocalizeKitTTS, check the [./main.py](`main.py`) file.

## 🙋‍♂️ Support
- If you have questions or issues:
- Check the troubleshooting section
- Open an issue on GitHub

## 🚀 Roadmap
- Graphical User Interface (GUI)
- Support for more input formats (PDF, DOCX)
- More video style options

## Third-Party Licenses

This project uses the following third-party libraries:

#### edge-tts
- **License**: MIT License
- **Usage**: Text-to-speech functionality using Microsoft Edge's TTS service
- **Copyright**: © 2021-2023 François Leblanc
- **Repository**: https://github.com/rany2/edge-tts