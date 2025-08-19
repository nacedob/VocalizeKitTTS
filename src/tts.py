import os
import json
import wave
import asyncio
import re
from typing import List, Tuple, Union, Optional
import edge_tts
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer


def format_srt_time(seconds: float) -> str:
    """
    Convert seconds into SRT time format (HH:MM:SS,mmm).
    Example: 65.32 -> "00:01:05,320"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def convert_to_wav(input_path: str, output_path: str) -> None:
    """
    Convert an audio file into mono WAV at 16kHz (recommended for Vosk).
    Supports formats like mp3, ogg, flac, etc.
    """
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")


class TTSEngine:
    """
    Text-to-Speech Engine using Microsoft Edge TTS and Vosk for transcription.
    - Converts structured text (HTML-like tuples) into audio.
    - Exports transcription with timestamps in SRT format.
    """

    def __init__(self, pace: float = 1.15, volume: float = 1.0) -> None:
        """
        Initialize the TTS engine.
        :param pace: Speaking rate multiplier (0 < pace < 2).
        :param volume: Volume multiplier (0 < volume < 2).
        """
        if not (0 < pace < 2):
            raise ValueError("Pace must be between 0 and 2.")
        if not (0 < volume < 2):
            raise ValueError("Volume must be between 0 and 2.")

        self.pace = int((pace - 1) * 100)  # Edge TTS expects percentage change
        self.volume = int((volume - 1) * 100)

    def _detect_language_from_text(self, text: str) -> str:
        """
        Detect language from text using common character patterns.
        Returns 'es' for Spanish, 'en' for English, or defaults to 'en'.
        """
        # Common Spanish characters and patterns
        spanish_patterns = [
            r'[áéíóúñü]',  # Spanish accented characters
            r'\b(y|el|la|los|las|un|una|unos|unas|es|son|soy|eres|es|somos|sois|son)\b',
            r'\b(que|de|no|a|en|por|con|para|mi|tu|su|nuestro|vuestro|su)\b'
        ]
        
        # Common English patterns
        english_patterns = [
            r'\b(the|and|you|that|for|with|are|this|from|have)\b',
            r'\b(ing|ed|tion|ment|able|ible|ness|ship|hood|dom)\b'  # Common English suffixes
        ]
        
        spanish_score = 0
        english_score = 0
        
        text_lower = text.lower()
        
        # Check for Spanish patterns
        for pattern in spanish_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            spanish_score += len(matches)
        
        # Check for English patterns
        for pattern in english_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            english_score += len(matches)
        
        # Also check for common Spanish words that might not be caught by patterns
        common_spanish_words = ['hola', 'gracias', 'por favor', 'adiós', 'buenos días', 'buenas tardes', 'buenas noches']
        for word in common_spanish_words:
            if word in text_lower:
                spanish_score += 3
        
        # Also check for common English words
        common_english_words = ['hello', 'thank you', 'please', 'goodbye', 'good morning', 'good afternoon', 'good evening']
        for word in common_english_words:
            if word in text_lower:
                english_score += 3
        
        # Return the detected language
        if spanish_score > english_score and spanish_score > 2:
            return 'es'
        elif english_score > spanish_score and english_score > 2:
            return 'en'
        else:
            # Default to English if unclear
            return 'en'

    def _get_voice_for_language(self, language: str) -> str:
        """
        Get appropriate voice for the specified language.
        :param language: Language code ("es" or "en")
        :return: Voice identifier string
        """
        voice_map = {
            "es": "es-MX-DaliaNeural",    # Mexican Spanish female
            "en": "en-US-AriaNeural"      # US English female
        }
        return voice_map.get(language, voice_map["en"])

    def _html_tuples_to_text(self, tuples: Union[Tuple[str, str], List[Tuple[str, str]]]) -> str:
        """
        Convert HTML-like (tag, text) tuples into plain text with pauses.
        Adds extra pauses based on tag importance (h1 > h2 > h3, etc.).
        """
        parts = []
        for tag, text in tuples:
            if tag == "h1":
                part = f". . . {text}. . ."
            elif tag == "h2":
                part = f". . {text}. ."
            elif tag in {"h3", "h4", "h5", "h6"}:
                part = f". {text}. "
            else:
                part = f"{text}. "
            parts.append(part)
        return " ".join(parts).strip()

    def text_to_audio(
        self, 
        html_tuples: Union[Tuple[str, str], List[Tuple[str, str]]], 
        output_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Convert structured text into audio (mp3 + wav).
        :param html_tuples: List of (tag, text) pairs, e.g. [("h1", "Title"), ("p", "Content")].
        :param output_path: Output mp3 path. A WAV copy is also generated.
        :param language: Language code ("es" for Spanish, "en" for English). If None, auto-detects.
        :return: Detected language code
        """
        if not isinstance(html_tuples, (tuple, list)) or not html_tuples:
            raise ValueError("Input must be a non-empty tuple or list of (tag, text).")

        allowed_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "strong", "em"}
        for i, (tag, text) in enumerate(html_tuples):
            if tag not in allowed_tags:
                raise ValueError(f"Invalid tag '{tag}' at index {i}. Allowed: {allowed_tags}")
            if not isinstance(text, str):
                raise TypeError(f"Text at index {i} must be str, got {type(text)}.")

        # Convert to plain text for language detection
        plain_text = self._html_tuples_to_text(html_tuples)
        
        # Auto-detect language if not specified
        if language is None:
            language = self._detect_language_from_text(plain_text)
        
        if language not in {"es", "en"}:
            raise ValueError("Language must be 'es' or 'en'.")

        voice = self._get_voice_for_language(language)
        
        mp3_path = output_path.replace(".wav", ".mp3")
        asyncio.run(self._generate_audio(plain_text, mp3_path, voice))

        # Convert audio to wav for transcription if needed
        if output_path.endswith(".wav"):
            convert_to_wav(mp3_path, output_path)
            # Delete temp mp3 file
            os.remove(mp3_path)
        
        return language

    async def _generate_audio(self, text: str, output_path: str, voice: str) -> None:
        """Internal async function to generate audio via Edge TTS."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        communicator = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=f"+{self.pace}%",
            volume=f"+{self.volume}%"
        )
        await communicator.save(output_path)

    def _transcribe_with_timings(
        self,
        audio_path: str,
        language: str,
        chunk_duration: float = 1.0
    ) -> Optional[List[dict]]:
        """
        Transcribe an audio file with word-level timings using Vosk.
        
        :param audio_path: Path to mono PCM WAV file.
        :param language: "en" or "es".
        :param chunk_duration: Length of audio (in seconds) to process per iteration.
                               Smaller values -> more frequent updates, finer granularity.
                               Larger values -> faster processing, but coarser segmentation.
        :return: List of transcription segments (dicts).
        """
        if language not in {"en", "es"}:
            raise ValueError(f"Language must be 'en' or 'es'. Got {language}")

        model_path = f"data/vosk_models/vosk-model-small-{language}"
        if not os.path.exists(model_path):
            print(f"⚠ Missing model at '{model_path}'. Download from https://alphacephei.com/vosk/models")
            return None

        model = Model(model_path)

        with wave.open(audio_path, "rb") as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                raise ValueError("Audio must be WAV mono PCM.")

            framerate = wf.getframerate()
            # Frames per chunk = seconds * frames/sec
            frames_per_chunk = int(chunk_duration * framerate)

            recognizer = KaldiRecognizer(model, framerate)
            recognizer.SetWords(True)  # Enable word-level timestamps

            results = []
            while True:
                data = wf.readframes(frames_per_chunk)
                if not data:
                    break
                if recognizer.AcceptWaveform(data):
                    results.append(json.loads(recognizer.Result()))

            results.append(json.loads(recognizer.FinalResult()))
            return results

    def create_srt_file(
        self,
        input_audio: str,
        output_srt: Optional[str] = None,
        language: Optional[str] = None,
        segment_duration: Optional[float] = 4.0
    ) -> str:
        """
        Create an SRT subtitle file from an audio transcription.
        If `segment_duration` is set, the SRT is split into fixed-length chunks (e.g. every 2s),
        instead of relying on Vosk's natural phrase segmentation.

        :param input_audio: Path to a WAV file.
        :param output_srt: Output path for SRT file. Defaults to input_audio with .srt extension.
        :param language: "en" or "es". If None, tries to auto-detect from filename or defaults to 'en'.
        :param segment_duration: If provided, subtitles are cut every N seconds.
        :return: Language code used for transcription
        """
        if not input_audio.endswith(".wav"):
            raise ValueError("Input audio must be a WAV file.")

        # Auto-detect language from filename if not provided
        if language is None:
            filename = os.path.basename(input_audio).lower()
            if any(x in filename for x in ['_es', '.es', 'spanish', 'español']):
                language = 'es'
            elif any(x in filename for x in ['_en', '.en', 'english', 'ingles']):
                language = 'en'
            else:
                language = 'en'  # Default to English

        if language not in {"en", "es"}:
            raise ValueError("Language must be 'es' or 'en'.")

        output_srt = output_srt or input_audio.replace(".wav", ".srt")

        transcription = self._transcribe_with_timings(input_audio, language)
        if not transcription:
            raise RuntimeError("Failed to transcribe audio.")

        # Collect all words with timings
        words = []
        for segment in transcription:
            for w in segment.get("result", []):
                words.append(w)
        
        os.makedirs(os.path.dirname(output_srt), exist_ok=True)
        with open(output_srt, "w", encoding="utf-8") as f:
            if segment_duration:
                # Fixed-time segmentation
                i, segment_start = 1, 0.0
                current_words = []

                for word in words:
                    word_start = word["start"]
                    word_end = word["end"]

                    # If the word passes the current segment limit, flush the segment
                    if word_start >= segment_start + segment_duration and current_words:
                        f.write(f"{i}\n")
                        f.write(f"{format_srt_time(segment_start)} --> {format_srt_time(current_words[-1]['end'])}\n")
                        f.write(" ".join(w["word"] for w in current_words) + "\n\n")
                        i += 1
                        segment_start += segment_duration
                        current_words = []

                    current_words.append(word)

                # Flush the last segment
                if current_words:
                    f.write(f"{i}\n")
                    f.write(f"{format_srt_time(segment_start)} --> {format_srt_time(current_words[-1]['end'])}\n")
                    f.write(" ".join(w["word"] for w in current_words) + "\n\n")

            else:
                # Natural segmentation (default Vosk behavior)
                i = 1
                for segment in transcription:
                    if not segment.get("result"):
                        continue

                    start_time = segment["result"][0]["start"]
                    end_time = segment["result"][-1]["end"]
                    text = " ".join(word["word"] for word in segment["result"])

                    f.write(f"{i}\n")
                    f.write(f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n")
                    f.write(f"{text}\n\n")
                    i += 1
        
        return language