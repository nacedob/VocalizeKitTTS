from icecream import ic
import pytest
import os
from src.preprocess import DocumentProcessor
from src.tts import TTSEngine  # Ajusta según tu estructura real

HTML_CONTENT = """
<html><body>
<h1>Este es el título principal</h1>
<h2>Este es el subtítulo</h2>
<p>Esto es un pareágrafo.</p>
<p>Esto es otro parrágrafo hecho para mirar la separacion de tiempos.</p>
<h2>Segundo subtítulo</h2>
<p>Esto es un tercer parágrafo.</p>
</body></html>
"""

@pytest.fixture
def temp_html_file():
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile('w', suffix=".html", encoding='utf-8', delete=False) as f:
        f.write(HTML_CONTENT)
        return f.name

def test_tts_audio_generation(temp_html_file):
    # Procesar HTML y convertir a texto con pausas
    processor = DocumentProcessor()
    ic(temp_html_file)
    tuples = processor.process_file(temp_html_file)
    ic(tuples)

    tts = TTSEngine()
    output = 'tests/output/test_tts.wav'
    tts.text_to_audio(tuples, output)
    
def test_create_srt(temp_html_file):
    # Procesar HTML y convertir a texto con pausas
    processor = DocumentProcessor()
    ic(temp_html_file)
    tuples = processor.process_file(temp_html_file)
    ic(tuples)

    tts = TTSEngine()
    audio_path = 'tests/output/test_tts.mp3'
    tts.text_to_audio(tuples, audio_path)
    srt_output = 'tests/output/test_tts.srt'
    tts.create_srt_file(audio_path.replace('.mp3', '.wav'), srt_output, 'es')
    assert os.path.exists(srt_output), f'{srt_output} not found'
    
    # Delete temporary files
    os.remove(audio_path)
    os.remove(audio_path.replace('.mp3', '.wav'))
    os.remove(srt_output)
    
# Check language
@pytest.fixture
def tts_engine():
    """Fixture to provide a TTSEngine instance for tests."""
    return TTSEngine()

def test_spanish_html_detection(tts_engine):
    """Test that Spanish HTML content is correctly detected."""
    spanish_html_tuples = [
        ("h1", "Artículo de Ejemplo"),
        ("h2", "Introducción al Contenido"),
        ("p", "Este es un párrafo de ejemplo en español que contiene texto con caracteres especiales como áéíóúñ."),
        ("p", "La tecnología ha avanzado mucho en los últimos años y ahora podemos disfrutar de muchas comodidades."),
        ("blockquote", "Esta es una cita importante que demuestra el funcionamiento del sistema."),
        ("p", "Finalmente, concluimos este artículo con algunas reflexiones finales sobre el tema.")
    ]
    
    detected_language = tts_engine.text_to_audio(spanish_html_tuples, "test_spanish.wav", language=None)
    assert detected_language == "es"

def test_english_html_detection(tts_engine):
    """Test that English HTML content is correctly detected."""
    english_html_tuples = [
        ("h1", "Example Article"),
        ("h2", "Content Introduction"),
        ("p", "This is an example paragraph in English that contains common words like the, and, for, with."),
        ("p", "Technology has advanced significantly in recent years and we can now enjoy many comforts."),
        ("blockquote", "This is an important quote that demonstrates the system's functionality."),
        ("p", "Finally, we conclude this article with some final thoughts on the topic.")
    ]
    
    detected_language = tts_engine.text_to_audio(english_html_tuples, "test_english.wav", language=None)
    assert detected_language == "en"

def test_spanish_with_accents(tts_engine):
    """Test Spanish detection with accented characters."""
    spanish_with_accents = [
        ("h1", "Artículo con Acentos"),
        ("p", "El pingüino caminó hacia el árbol y vio una canción."),
        ("p", "Esto es fácil de entender para cualquiera que hable español.")
    ]
    
    detected_language = tts_engine.text_to_audio(spanish_with_accents, "test_accents.wav", language=None)
    assert detected_language == "es"

def test_english_technical_content(tts_engine):
    """Test English detection with technical content."""
    english_technical = [
        ("h1", "Technical Documentation"),
        ("p", "The implementation of this functionality requires careful consideration of the underlying architecture."),
        ("p", "Development and testing are essential components of the software engineering process.")
    ]
    
    detected_language = tts_engine.text_to_audio(english_technical, "test_technical.wav", language=None)
    assert detected_language == "en"

def test_manual_spanish_override(tts_engine):
    """Test that manual Spanish language override works."""
    english_content = [
        ("h1", "This is English"),
        ("p", "But we want to force Spanish voice")
    ]
    
    detected_language = tts_engine.text_to_audio(english_content, "test_override_es.wav", language="es")
    assert detected_language == "es"

def test_manual_english_override(tts_engine):
    """Test that manual English language override works."""
    spanish_content = [
        ("h1", "Esto es Español"),
        ("p", "Pero queremos forzar voz en inglés")
    ]
    
    detected_language = tts_engine.text_to_audio(spanish_content, "test_override_en.wav", language="en")
    assert detected_language == "en"

def test_short_spanish_text(tts_engine):
    """Test detection with very short Spanish text."""
    short_spanish = [
        ("h1", "Hola mundo"),
        ("p", "Buenos días, ¿cómo estás?")
    ]
    
    detected_language = tts_engine.text_to_audio(short_spanish, "test_short_es.wav", language=None)
    assert detected_language == "es"

def test_short_english_text(tts_engine):
    """Test detection with very short English text."""
    short_english = [
        ("h1", "Hello world"),
        ("p", "Good morning, how are you?")
    ]
    
    detected_language = tts_engine.text_to_audio(short_english, "test_short_en.wav", language=None)
    assert detected_language == "en"

def test_mixed_content_defaults_to_english(tts_engine):
    """Test that mixed content defaults to English."""
    mixed_content = [
        ("h1", "Mixed Title"),
        ("p", "Hello hola thank you gracias please por favor."),
        ("p", "This is a mixed paragraph with some Spanish and English words.")
    ]
    
    detected_language = tts_engine.text_to_audio(mixed_content, "test_mixed.wav", language=None)
    assert detected_language == "en"

def test_empty_content_raises_error(tts_engine):
    """Test that empty content raises appropriate error."""
    with pytest.raises(ValueError, match="Input must be a non-empty tuple or list"):
        tts_engine.text_to_audio([], "test_empty.wav", language=None)

def test_invalid_language_raises_error(tts_engine):
    """Test that invalid language parameter raises error."""
    content = [("p", "Test content")]
    
    with pytest.raises(ValueError, match="Language must be 'es' or 'en'"):
        tts_engine.text_to_audio(content, "test_invalid.wav", language="fr")

def test_invalid_tag_raises_error(tts_engine):
    """Test that invalid HTML tag raises error."""
    invalid_content = [("invalid_tag", "Some content")]
    
    with pytest.raises(ValueError, match="Invalid tag 'invalid_tag'"):
        tts_engine.text_to_audio(invalid_content, "test_invalid_tag.wav", language=None)

def test_non_text_content_raises_error(tts_engine):
    """Test that non-string text content raises error."""
    invalid_content = [("p", 123)]  # Integer instead of string
    
    with pytest.raises(TypeError, match="Text at index 0 must be str"):
        tts_engine.text_to_audio(invalid_content, "test_non_text.wav", language=None)

# Test the language detection function directly
def test_detect_language_from_text_spanish(tts_engine):
    """Test direct language detection with Spanish text."""
    spanish_text = "Este es un texto en español con caracteres como áéíóúñ y palabras comunes como el, la, y, de."
    detected = tts_engine._detect_language_from_text(spanish_text)
    assert detected == "es"

def test_detect_language_from_text_english(tts_engine):
    """Test direct language detection with English text."""
    english_text = "This is an English text with common words like the, and, for, with, and typical suffixes like ing, ed, tion."
    detected = tts_engine._detect_language_from_text(english_text)
    assert detected == "en"

def test_detect_language_from_text_mixed(tts_engine):
    """Test direct language detection with mixed text."""
    mixed_text = "Hello hola thank you gracias this is a mixed text example."
    detected = tts_engine._detect_language_from_text(mixed_text)
    assert detected == "en"  # Should default to English

def test_detect_language_from_text_short_spanish(tts_engine):
    """Test direct language detection with short Spanish text."""
    short_spanish = "Hola mundo"
    detected = tts_engine._detect_language_from_text(short_spanish)
    assert detected == "es"

def test_detect_language_from_text_short_english(tts_engine):
    """Test direct language detection with short English text."""
    short_english = "Hello world"
    detected = tts_engine._detect_language_from_text(short_english)
    assert detected == "en"

# Parametrized tests for edge cases
@pytest.mark.parametrize("text,expected_lang", [
    ("", "en"),  # Empty string defaults to English
    ("1234567890", "en"),  # Numbers only defaults to English
    ("!@#$%^&*()", "en"),  # Symbols only defaults to English
    ("á é í ó ú", "es"),  # Just Spanish accents
    ("hello hola", "en"),  # Mixed but more English-like
    ("hola hello", "es"),  # Mixed but more Spanish-like
])
def test_edge_cases_language_detection(tts_engine, text, expected_lang):
    """Test various edge cases for language detection."""
    detected = tts_engine._detect_language_from_text(text)
    assert detected == expected_lang