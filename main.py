# main.py
"""
Simple main script to process HTML files into audio, subtitles, and videos.
"""

import os
import sys
from pathlib import Path
from src.preprocess import DocumentProcessor
from src.tts import TTSEngine
from src.videocreator import VideoCreator
from src.logger import Logger
from src.utils import create_output_directories, format_spanish_date_from_path

def main():
    # Configuration
    input_folder = "data/example"
    output_folder = "data/example/output"
    background_music_path = "data/example/background_music.mp3"
    background_image_path = "data/example/background_image.jpg"
    
    # Create output directories
    create_output_directories(output_folder)
    
    # Initialize components
    logger = Logger()
    preprocessor = DocumentProcessor()
    audiogenerator = TTSEngine()
    videocreator = VideoCreator(output_folder=f'{output_folder}/video', logger=logger)
    
    # Process each HTML file
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.html'):
            file_path = os.path.join(input_folder, filename)
            
            # Process HTML to audio
            logger.print(f"Processing: {filename}", color="yellow")
            html_tuples = preprocessor.process_file(file_path, save_transcript=False)
            logger.print(f"HTML processed: {len(html_tuples)} tuples", color="green")
            
            # Generate audio file
            logger.print("Generating audio...", color="blue")
            base_name = os.path.splitext(filename)[0]
            audio_path = os.path.join(output_folder, "audio", f"{base_name}.wav")
            lang = audiogenerator.text_to_audio(html_tuples, audio_path)
            logger.print(f"Audio created: {audio_path}. Detected language: {lang}", color="green")
            
            # Generate subtitles
            logger.print("Generating subtitles...", color="blue")
            srt_path = os.path.join(output_folder, "subtitles", f"{base_name}.srt")
            audiogenerator.create_srt_file(audio_path, srt_path, language='es')
            logger.print(f"Subtitles created: {srt_path}", color="green")
            
            # Create video
            video_path = os.path.join(output_folder, "video", f"{base_name}.mp4")
            date_title = format_spanish_date_from_path(input_folder) or "Sample Content"
            
            logger.print("Creating video...", color="blue")
            videocreator.create_video(
                voice_path=audio_path,
                background_music_path=background_music_path,
                picture_path=background_image_path,
                srt_file=srt_path,
                text=date_title,
                output_path=video_path
            )
            logger.print(f"Video created: {video_path}", color="green")
    
    logger.print("All files processed successfully!", color="green")

if __name__ == '__main__':
    main()