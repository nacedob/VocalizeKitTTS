import os
import re
import logging
from typing import List, Tuple, Optional, Dict, Set, Union
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString, Tag

# Configure logging
logger = logging.getLogger(__name__)

class DocumentProcessor:
    # Common HTML tags to extract with their priority for processing
    HTML_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'li', 'strong', 'em', 'div', 'span'}
    
    # Patterns for detecting chapter headings in various languages
    CHAPTER_PATTERNS = {
        'es': re.compile(r'cap[ií]tulo|capítulo|secci[oó]n|parte', re.IGNORECASE),
        'en': re.compile(r'chapter|section|part', re.IGNORECASE),
        'fr': re.compile(r'chapitre|section|partie', re.IGNORECASE),
        'de': re.compile(r'kapitel|abschnitt|teil', re.IGNORECASE)
    }
    
    def __init__(self, language: str = 'es'):
        """
        Initialize DocumentProcessor with optional language support.
        
        Args:
            language: Language code for chapter pattern detection ('es', 'en', 'fr', 'de')
        """
        self.language = language
        self.chapter_pattern = self.CHAPTER_PATTERNS.get(language, self.CHAPTER_PATTERNS['es'])

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text by removing extra whitespace and normalizing.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove non-printable characters except common punctuation
        text = re.sub(r'[^\x20-\x7E\u00A0-\u024F\u1E00-\u1EFF]', ' ', text)
        return text

    def _is_valid_content(self, text: str, min_length: int = 3) -> bool:
        """
        Check if text contains valid content worth processing.
        
        Args:
            text: Text to validate
            min_length: Minimum character length to consider valid
            
        Returns:
            Boolean indicating if text is valid
        """
        if not text or len(text.strip()) < min_length:
            return False
        
        # Check if text contains mostly non-alphanumeric characters
        alpha_count = sum(1 for char in text if char.isalpha())
        if alpha_count < min_length:
            return False
            
        return True

    def _process_epub(self, file_path: str) -> List[Tuple[str, str]]:
        """
        Process EPUB file and extract structured content.
        
        Args:
            file_path: Path to EPUB file
            
        Returns:
            List of (tag, text) tuples
        """
        result: List[Tuple[str, str]] = []
        
        try:
            book = epub.read_epub(file_path)
            logger.info(f"Processing EPUB: {file_path}")
            
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                try:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    # Process all relevant tags
                    for tag in soup.find_all(list(self.HTML_TAGS)):
                        text = self._clean_text(tag.get_text())
                        
                        if not self._is_valid_content(text):
                            continue
                            
                        # Handle chapter detection
                        tag_name = tag.name
                        if tag_name == 'p' and self.chapter_pattern.search(text):
                            tag_name = 'h1'  # Promote to heading
                            
                        result.append((tag_name, text))
                        
                except Exception as e:
                    logger.warning(f"Error processing EPUB item: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to process EPUB {file_path}: {e}")
            raise
            
        logger.info(f"Extracted {len(result)} content items from EPUB")
        return result

    def _process_html(self, file_path: str, save_transcript: bool = False) -> List[Tuple[str, str]]:
        """
        Process HTML file and extract structured content.
        
        Args:
            file_path: Path to HTML file
            save_transcript: Whether to save a text transcript
            
        Returns:
            List of (tag, text) tuples
        """
        result: List[Tuple[str, str]] = []
        transcript: List[str] = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html = f.read()

            soup = BeautifulSoup(html, 'html.parser')
            logger.info(f"Processing HTML: {file_path}")

            def process_element(element: Tag, depth: int = 0) -> None:
                """Recursively process HTML elements."""
                if depth > 10:  # Prevent infinite recursion
                    return
                    
                # Process current element if it's a relevant tag
                if element.name in self.HTML_TAGS:
                    text = self._clean_text(element.get_text())
                    
                    if self._is_valid_content(text):
                        result.append((element.name, text))
                        transcript.append(text)
                
                # Process children recursively
                for child in element.children:
                    if isinstance(child, Tag):
                        process_element(child, depth + 1)

            # Start processing from body or root
            start_element = soup.body or soup
            process_element(start_element)
            
            # Save transcript if requested
            if save_transcript and transcript:
                transcript_path = Path(file_path).with_suffix('.txt')
                transcript_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(transcript))
                logger.info(f"Transcript saved to: {transcript_path}")
                
        except Exception as e:
            logger.error(f"Failed to process HTML {file_path}: {e}")
            raise
            
        logger.info(f"Extracted {len(result)} content items from HTML")
        return result

    def _process_txt(self, file_path: str) -> List[Tuple[str, str]]:
        """
        Process plain text file and extract content as paragraphs.
        
        Args:
            file_path: Path to text file
            
        Returns:
            List of (tag, text) tuples (all as 'p' tags)
        """
        result: List[Tuple[str, str]] = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Split into paragraphs (empty lines as separators)
            paragraphs = re.split(r'\n\s*\n', content)
            
            for paragraph in paragraphs:
                text = self._clean_text(paragraph)
                if self._is_valid_content(text):
                    result.append(('p', text))
                    
        except Exception as e:
            logger.error(f"Failed to process text file {file_path}: {e}")
            raise
            
        logger.info(f"Extracted {len(result)} paragraphs from text file")
        return result

    def process_file(self, file_path: str, save_transcript: bool = False) -> List[Tuple[str, str]]:
        """
        Process a file and extract structured content.
        
        Args:
            file_path: Path to the file to process
            save_transcript: Whether to save a text transcript (for HTML files)
            
        Returns:
            List of (tag, text) tuples representing the document structure
            
        Raises:
            ValueError: If file extension is not supported
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_path = os.path.abspath(file_path)
        ext = Path(file_path).suffix.lower()
        
        logger.info(f"Processing file: {file_path}")
        
        try:
            if ext == '.epub':
                return self._process_epub(file_path)
            elif ext == '.html' or ext == '.htm':
                return self._process_html(file_path, save_transcript)
            elif ext == '.txt':
                return self._process_txt(file_path)
            else:
                raise ValueError(f'Unsupported file extension: {ext}. Supported: .epub, .html, .htm, .txt')
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise

    def batch_process(self, directory_path: str, extensions: List[str] = None) -> Dict[str, List[Tuple[str, str]]]:
        """
        Process all supported files in a directory.
        
        Args:
            directory_path: Path to directory containing files
            extensions: List of file extensions to process (default: all supported)
            
        Returns:
            Dictionary mapping filenames to their processed content
        """
        if extensions is None:
            extensions = ['.epub', '.html', '.htm', '.txt']
            
        results = {}
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
            
        for ext in extensions:
            for file_path in directory_path.glob(f'*{ext}'):
                if file_path.is_file():
                    try:
                        content = self.process_file(str(file_path))
                        results[file_path.name] = content
                    except Exception as e:
                        logger.warning(f"Skipping file {file_path}: {e}")
                        continue
                        
        return results

# Example usage and quick test
if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test the processor
    processor = DocumentProcessor(language='es')
    
    # Example files (would need to exist)
    test_files = [
        'sample.epub',
        'sample.html',
        'sample.txt'
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                result = processor.process_file(test_file)
                print(f"Processed {test_file}: {len(result)} items")
                for i, (tag, text) in enumerate(result[:3]):  # Show first 3 items
                    print(f"  {i+1}. [{tag}] {text[:50]}...")
            except Exception as e:
                print(f"Error processing {test_file}: {e}")