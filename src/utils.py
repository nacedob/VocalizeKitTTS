"""
Utility functions for file processing and date formatting.
"""

import os
import re
import locale
from datetime import datetime
from typing import Optional
from pathlib import Path

def create_output_directories(output_folder: str) -> None:
    """
    Create necessary output directories for audio, subtitles, and video.
    
    Args:
        output_folder: Base output directory path
    """
    directories = [
        output_folder,
        os.path.join(output_folder, "audio"),
        os.path.join(output_folder, "subtitles"), 
        os.path.join(output_folder, "video")
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def extract_date_from_path(path: str) -> Optional[str]:
    """
    Extract date string from path using pattern matching.
    
    Args:
        path: File or directory path potentially containing a date
        
    Returns:
        Date string in YYMMDD format or None if not found
    """
    # Look for 6-digit date patterns (YYMMDD)
    match = re.search(r'(\d{6})', os.path.basename(path))
    return match.group(1) if match else None

def format_spanish_date(date_str: str) -> Optional[str]:
    """
    Format a date string (YYMMDD) into Spanish text format.
    
    Args:
        date_str: Date string in YYMMDD format
        
    Returns:
        Formatted Spanish date string or None if invalid
    """
    try:
        date_obj = datetime.strptime(date_str, "%y%m%d")
        
        # Try to set Spanish locale
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'Spanish_Spain')
            except locale.Error:
                # Fallback to English if Spanish locale not available
                return date_obj.strftime("%d %B %Y")
        
        formatted = date_obj.strftime("%d %B %Y").capitalize()
        return formatted
        
    except ValueError:
        return None

def format_spanish_date_from_path(path: str) -> Optional[str]:
    """
    Extract and format date from path into Spanish text.
    
    Args:
        path: Path containing date information
        
    Returns:
        Formatted Spanish date or None if no date found
    """
    date_str = extract_date_from_path(path)
    if not date_str:
        return None
        
    return format_spanish_date(date_str)

def get_available_files(directory: str, extensions: list) -> list:
    """
    Get list of files with specified extensions in directory.
    
    Args:
        directory: Directory to search
        extensions: List of file extensions to include
        
    Returns:
        List of file paths matching the extensions
    """
    if not os.path.exists(directory):
        return []
        
    return [
        os.path.join(directory, f) for f in os.listdir(directory)
        if any(f.lower().endswith(ext) for ext in extensions)
    ]

def validate_file_path(file_path: str, file_type: str = "file") -> bool:
    """
    Validate that a file or directory exists.
    
    Args:
        file_path: Path to validate
        file_type: Type of path ('file' or 'directory')
        
    Returns:
        True if path exists and is correct type, False otherwise
    """
    if file_type == "file":
        return os.path.isfile(file_path)
    elif file_type == "directory":
        return os.path.isdir(file_path)
    return os.path.exists(file_path)