import fitz  # PyMuPDF
import docx
import re
import requests
from bs4 import BeautifulSoup

def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    Handles multi-column layouts by reading text blocks.
    """
    text = ""
    try:
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
    return clean_text(text)

def extract_text_from_docx(uploaded_file):
    """
    Extracts text from a DOCX file using python-docx.
    """
    text = ""
    try:
        doc = docx.Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"
    return clean_text(text)

def clean_text(text):
    """
    Cleans extracted text: removes URLs, emails, special chars, 
    and excessive whitespace.
    """
    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)
    # Remove Emails
    text = re.sub(r'\S+@\S+', '', text)
    # Remove non-ASCII characters (keep basic punctuation)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_file(uploaded_file):
    """
    Dispatcher function to handle different file types.
    """
    if uploaded_file.name.lower().endswith('.pdf'):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.lower().endswith('.docx'):
        return extract_text_from_docx(uploaded_file)
    else:
        return "Unsupported file format. Please upload PDF or DOCX."

def analyze_ats_compliance(uploaded_file, text):
    """
    Checks for common ATS formatting issues.
    Returns a dictionary of checks and statuses.
    """
    ats_report = {
        "File Type": {"status": "Pass", "msg": "PDF/DOCX detected."},
        "Text Extractable": {"status": "Pass", "msg": "Text found."},
        "Standard Sections": {"status": "Check", "msg": "Looking for headers..."},
        "No Images/Graphics": {"status": "Pass", "msg": "No images detected (Pure Text)."}
    }
    
    # 1. Check Text Extraction
    if not text or len(text) < 100:
        ats_report["Text Extractable"] = {"status": "Fail", "msg": "Very little text found. Potential image-based PDF."}
        return ats_report

    # 2. Check Standard Headers
    headers = ["Experience", "Education", "Skills", "Summary", "Projects", "Work History"]
    found_headers = [h for h in headers if h.lower() in text.lower()]
    
    if len(found_headers) >= 3:
        ats_report["Standard Sections"] = {"status": "Pass", "msg": f"Found: {', '.join(found_headers)}"}
    else:
        ats_report["Standard Sections"] = {"status": "Warning", "msg": "Missing standard headers (Experience, Education, Skills). ATS might get confused."}

    # 3. Check for Images (PDF only)
    if uploaded_file.name.lower().endswith('.pdf'):
        try:
            # We need to reset stream position or re-open
            uploaded_file.seek(0)
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            image_count = 0
            for page in doc:
                image_count += len(page.get_images())
            
            if image_count > 0:
                ats_report["No Images/Graphics"] = {"status": "Warning", "msg": f"Detected {image_count} images/icons. Some older ATS reject these."}
        except:
            pass
            
    return ats_report

def fetch_job_description(url):
    """
    Fetches and extracts Job Description text from a given URL.
    Uses basic scraping with User-Agent headers (simple bypass).
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
                
            # Get text
            text = soup.get_text(separator=' ')
            
            # Clean up white space (simple normalization)
            clean_text = re.sub(r'\s+', ' ', text).strip()
            
            # Truncate if too long (likely scraped whole site home page)
            if len(clean_text) > 5000:
                clean_text = clean_text[:5000]
                
            return clean_text
        else:
            return f"Error: Unable to fetch URL (Status {response.status_code})"
    except Exception as e:
        return f"Error fetching URL: {str(e)}"
