# Import PyPDF2 and the CrewAI tool decorator.
# Create a @tool named 'Read_PDF_Circular'.
# It should take a file path as input, read the PDF, and return the extracted text as a single string.
# Add basic error handling if the file is not found.


import os
from typing import Optional
from pypdf import PdfReader
import pdfplumber
from crewai.tools import tool


@tool
def read_pdf_circular(file_path: str) -> str:
    """
    Read a PDF circular and return the extracted text as a single string.

    Args:
        file_path: Path to the PDF file to read.

    Returns:
        Extracted text from all pages as a single string.

    Raises:
        FileNotFoundError: If the file is not found.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    reader = PdfReader(file_path)
    text_parts = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)

    return "\n\n".join(text_parts)


@tool
def read_pdf_with_paragraphs(file_path: str) -> str:
    """
    Read a PDF file using pdfplumber, maintaining paragraph structure.

    Args:
        file_path: Path to the PDF file to read.

    Returns:
        Extracted text from all pages as a single concatenated string,
        with paragraph structure preserved.

    Raises:
        FileNotFoundError: If the file is not found.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    text_parts = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

    return "\n\n".join(text_parts)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.
    Returns the concatenated text content from all pages.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(pdf_path)
    text_parts = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)

    return "\n\n".join(text_parts)


def extract_text_with_page_numbers(pdf_path: str) -> list[dict]:
    """
    Extract text from PDF with page number tracking.
    Returns a list of dicts: [{"page": 1, "text": "..."}, ...]
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(pdf_path)
    pages_data = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            pages_data.append({"page": page_num, "text": text})

    return pages_data


def get_pdf_metadata(pdf_path: str) -> dict:
    """
    Extract PDF metadata (author, title, creator, etc.).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(pdf_path)
    metadata = reader.metadata or {}

    return {
        "author": metadata.get("/Author", ""),
        "title": metadata.get("/Title", ""),
        "creator": metadata.get("/Creator", ""),
        "producer": metadata.get("/Producer", ""),
        "page_count": len(reader.pages),
    }
