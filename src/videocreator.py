from icecream import ic
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    TextClip,
    CompositeVideoClip,
    CompositeAudioClip,
)
from moviepy.video.tools.subtitles import file_to_subtitles, SubtitlesClip
from typing import Optional
from src.logger import Logger
import os
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})


class VideoCreator:
    def __init__(self, output_folder: str, logger: Optional[Logger] = None, color: Optional[str] = "gray") -> None:
        self.output_folder = output_folder
        self.logger = logger
        self.color = color

    def _log(self, text: str, color: str = 'gray') -> None:
        use_color = color if color is not None else self.color
        if self.logger:
            self.logger.print(text, color=use_color)
        else:
            print(text)
            
    def _create_subtitles_clip(self, srt_file: str, video_size: tuple) -> SubtitlesClip:
        """Create a subtitles clip from SRT file with custom styling"""
        def make_text(txt):
            """Helper function to style each subtitle"""
            return TextClip(
                txt.upper(),  # Convert to uppercase
                font='Arial',
                fontsize=22,
                color='yellow',
                stroke_color='black',
                stroke_width=0.5,
                size=(video_size[0] * 0.9, None),  # 90% of video width
                method='caption',
                align='center'
            )
        
        # Parse SRT file and create subtitles clip
        subs = file_to_subtitles(srt_file)
        return SubtitlesClip(subs, make_text)

    def create_video(
        self,
        voice_path: str,
        background_music_path: str,
        picture_path: str,
        background_volume: float = 0.3,
        srt_file: Optional[str] = None,
        text: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> None:
        self._log("Loading voice audio...")
        voice_clip = AudioFileClip(voice_path)
        duration = voice_clip.duration

        self._log("Loading background music and adjusting volume...")
        bg_music = AudioFileClip(background_music_path).volumex(background_volume).subclip(0, duration)

        self._log("Loading background image...")
        image_clip = ImageClip(picture_path).set_duration(duration).set_fps(24)

        # Create base clips list
        clips = [image_clip]

        # Add optional text overlay (removed the text=False override)
        if text:
            self._log("Creating text overlay...")
            text_clip = TextClip(
                text,
                fontsize=16,
                color="#e39b3f",
                font="Arial",
                method='caption',
                size=(int(image_clip.w * 0.9), None),
                align='center'
            ).set_position(("center", "bottom")).set_duration(duration)
            clips.append(text_clip)

        # Add subtitles if SRT file provided
        if srt_file and os.path.exists(srt_file):
            self._log("Adding subtitles...")
            subs_clip = self._create_subtitles_clip(srt_file, (image_clip.w, image_clip.h))
            subs_clip = subs_clip.set_position(('center', 'bottom')).set_duration(duration)
            clips.append(subs_clip)

        # Compose final video
        final_video = CompositeVideoClip(clips)

        self._log("Combining audio tracks...")
        mixed_audio = CompositeAudioClip([bg_music, voice_clip.set_duration(duration)])
        final_video = final_video.set_audio(mixed_audio)

        if output_path is None:
            voice_filename = os.path.splitext(os.path.basename(voice_path))[0]
            video_filename = f"{voice_filename}.mp4"
            output_path = os.path.join(self.output_folder, video_filename)
        
        self._log(f"Writing final video to {output_path}...")
        final_video.write_videofile(
            output_path,
            fps=12,
            codec='libx264',
            audio_codec='aac',
            logger=None
        )
        self._log("Video creation completed!", color="green")