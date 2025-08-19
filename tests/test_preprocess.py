import pytest
from tempfile import NamedTemporaryFile
from src.preprocess import DocumentProcessor  # ajusta el import según dónde esté la clase
import os

TEST_HTML = """
<html>
    <body>
        <h1>Title H1</h1>
        <h2>Subtitle H2</h2>
        <p>This is a paragraph.</p>
        <blockquote>Some quote here.</blockquote>
        <img src="image.jpg" alt="An image that should be ignored"/>
    </body>
</html>
"""

@pytest.fixture
def temp_html_file():
    with NamedTemporaryFile('w', suffix=".html", encoding='utf-8', delete=False) as f:
        f.write(TEST_HTML)
        path = f.name
    yield path
    os.unlink(path)

def test_process_html_ignores_images(temp_html_file):
    
    processor = DocumentProcessor()
    result = processor.process_file(temp_html_file)

    expected = [
        ('h1', 'Title H1'),
        ('h2', 'Subtitle H2'),
        ('p', 'This is a paragraph.'),
        ('blockquote', 'Some quote here.')
        # La etiqueta img no tiene texto, por eso no aparece
    ]

    assert result == expected


def test_save_transcript(temp_html_file):
    processor = DocumentProcessor()
    result = processor.process_file(temp_html_file, save_transcript=True)
    output_path = temp_html_file.replace('html', 'txt')
    assert os.path.exists(output_path), f'{output_path} not found'
    # Read content
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert content == (
        'Title H1\n'
        'Subtitle H2\n'
        'This is a paragraph.\n'
        'Some quote here.'
    )
if __name__ == "__main__":
    pytest.main()