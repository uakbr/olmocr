#!/usr/bin/env python3
"""
Text formatting utilities for OCR output to improve readability and formatting.
"""

import re
import markdown
import textwrap
from typing import List, Dict, Any, Optional


def remove_excessive_spaces(text: str) -> str:
    """
    Remove excessive spaces from OCR output.
    - Replace multiple spaces with a single space
    - Remove spaces at the beginning of lines
    - Preserve paragraph separation
    """
    # Replace multiple spaces with a single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove spaces at the beginning of lines
    text = re.sub(r'(?m)^ +', '', text)
    
    # Normalize newlines (replace multiple newlines with two newlines for paragraph separation)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def fix_line_breaks(text: str) -> str:
    """
    Fix incorrect line breaks by joining sentences that were split across lines.
    """
    # Join lines that don't end with punctuation and are not followed by a capitalized word or blank line
    lines = text.split('\n')
    result_lines = []
    
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            
            # If current line is empty, add it as is
            if not line.strip():
                result_lines.append(line)
                continue
                
            # If current line doesn't end with punctuation, and next line doesn't start with capital
            # and next line isn't empty, join them
            if (not line.strip().endswith(('.', '!', '?', ':', ';', '"', ')', ']', '}'))) and \
               next_line and not next_line[0].isupper() and not next_line.startswith(('-', '•', '*')):
                result_lines.append(line + ' ')
            else:
                result_lines.append(line)
        else:
            result_lines.append(line)
    
    return '\n'.join(result_lines)


def detect_and_format_paragraphs(text: str) -> str:
    """
    Detect paragraphs and format them with proper spacing.
    """
    # Split by empty lines to get paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        # Join lines within paragraph if they don't end with period
        paragraph = fix_line_breaks(paragraph)
        formatted_paragraphs.append(paragraph.strip())
    
    # Join paragraphs with double newlines
    return '\n\n'.join(formatted_paragraphs)


def format_academic_structure(text: str) -> str:
    """
    Format academic structure elements like headings, sections, and citations.
    """
    # Format section headings (numbered sections)
    text = re.sub(r'(?m)^(\d+\.?\d*\.?\s+[A-Z][^\.]+)$', r'## \1', text)
    
    # Format paper title (usually at the beginning)
    lines = text.split('\n')
    if len(lines) > 0 and not lines[0].startswith('#'):
        lines[0] = '# ' + lines[0]
        text = '\n'.join(lines)
    
    # Format lists
    text = re.sub(r'(?m)^(\d+\.\s+)(.+)$', r'\1\2', text)
    
    # Format citations
    text = re.sub(r'\[(\d+)\]', r'[<sup>\1</sup>]', text)
    
    return text


def convert_to_markdown(text: str) -> str:
    """
    Convert the formatted text to Markdown format.
    """
    # Apply all formatting functions
    text = remove_excessive_spaces(text)
    text = detect_and_format_paragraphs(text)
    text = format_academic_structure(text)
    
    return text


def post_process_ocr_text(text: str, format_as_markdown: bool = False) -> str:
    """
    Main function to post-process OCR text.
    
    Args:
        text: Raw OCR text to process
        format_as_markdown: Whether to format the output as Markdown (default: False)
    
    Returns:
        Processed text with improved formatting
    """
    # Apply basic cleanup
    text = remove_excessive_spaces(text)
    text = detect_and_format_paragraphs(text)
    
    if format_as_markdown:
        text = format_academic_structure(text)
    
    return text


def convert_markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown text to HTML.
    """
    return markdown.markdown(markdown_text, extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists', 'attr_list'])


def process_page_text(page_text: str, use_markdown: bool = False) -> str:
    """
    Process a single page's text.
    
    Args:
        page_text: Raw OCR text for a single page
        use_markdown: Whether to use Markdown formatting
    
    Returns:
        Processed text with improved formatting
    """
    processed_text = post_process_ocr_text(page_text, format_as_markdown=use_markdown)
    
    if use_markdown:
        return convert_markdown_to_html(processed_text)
    
    return processed_text 