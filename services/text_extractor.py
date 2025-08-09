import fitz  # PyMuPDF
from docx import Document
import os
import re
from typing import Tuple


class TextExtractor:
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF file using PyMuPDF"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extract text from DOCX file using python-docx"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting DOCX text: {e}")
            return ""
    
    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Error extracting TXT text: {e}")
            return ""
    
    @staticmethod
    def extract_name_from_text(text: str, filename: str) -> str:
        """Extract candidate name from resume text or use filename"""
        try:
            # Look for name patterns in the first few lines
            lines = text.split('\n')[:5]
            for line in lines:
                line = line.strip()
                # Simple name pattern: 2-3 words, each starting with capital letter
                name_match = re.search(r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$', line)
                if name_match:
                    return name_match.group(1)
            
            # Fallback to filename without extension
            return os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
        except Exception:
            return os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
    
    @staticmethod
    def process_file(file_path: str, filename: str) -> Tuple[str, str]:
        """Process a file and return (candidate_name, extracted_text)"""
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext == '.pdf':
            text = TextExtractor.extract_text_from_pdf(file_path)
        elif file_ext == '.docx':
            text = TextExtractor.extract_text_from_docx(file_path)
        elif file_ext == '.txt':
            text = TextExtractor.extract_text_from_txt(file_path)
        else:
            text = ""
        
        if not text:
            return filename, ""
        
        candidate_name = TextExtractor.extract_name_from_text(text, filename)
        return candidate_name, text