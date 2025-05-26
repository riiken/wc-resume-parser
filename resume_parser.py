import os
import io
import fitz  # PyMuPDF
import pdfplumber
import docx
from PIL import Image
import pytesseract
import json
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Extract raw text from resume file
def extract_text_from_resume(filename: str, content: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(content)
    elif ext == ".docx":
        return extract_text_from_docx(content)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return extract_text_from_image(content)
    else:
        return "Unsupported file format."

# PDF text extractor (with fallback to OCR)
def extract_text_from_pdf(content: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    if not text.strip():
        text = extract_text_from_pdf_with_ocr(content)

    return text

import fitz  # PyMuPDF
import easyocr
from PIL import Image
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

def extract_text_from_pdf_with_ocr(content: bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    text = ""
    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_np = np.array(img)
        result = reader.readtext(img_np, detail=0)
        text += "\n".join(result) + "\n"
    return text


# DOCX text extractor
def extract_text_from_docx(content: bytes) -> str:
    doc = docx.Document(io.BytesIO(content))
    return "\n".join([para.text for para in doc.paragraphs])

# Image text extractor (OCR)
def extract_text_from_image(content: bytes) -> str:
    image = Image.open(io.BytesIO(content)).convert("RGB")
    img_np = np.array(image)
    result = reader.readtext(img_np, detail=0)
    return "\n".join(result)

# Transform raw resume text to structured JSON using OpenAI
def transform_text_to_resume_data(raw_text: str) -> dict:
    prompt = f"""
You are a resume parser. Extract structured resume data in the following JSON format.

Expected JSON:
{{
  "id": null,
  "targetJobTitle": "",
  "targetJobDescription": "",
  "personalInfo": {{
    "fullName": "",
    "jobTitle": "",
    "email": "",
    "phone": "",
    "location": "",
    "summary": "",
    "profilePicture": null
  }},
  "sections": [
    {{
      "id": "null",
      "type": "experience",
      "title": "Work Experience",
      "order": 0,
      "hidden": false,
      "items": [
        {{
          "jobTitle": "",
          "company": "",
          "location": "",
          "startDate": null,
          "endDate": null,
          "currentPosition": false,
          "description": ""
        }}
      ],
      "groups": [],
      "state": {{}}
    }},
    {{
      "id": "null",
      "type": "projects",
      "title": "Projects",
      "order": 1,
      "hidden": false,
      "items": [],
      "groups": [],
      "state": {{}}
    }},
    {{
      "id": "null",
      "type": "education",
      "title": "Education",
      "order": 2,
      "hidden": false,
      "items": [],
      "groups": [],
      "state": {{}}
    }},
    {{
      "id": "null",
      "type": "skills",
      "title": "Skills",
      "order": 3,
      "format": "grouped",
      "items": [],
      "groups": [],
      "state": {{
        "categoryOrder": [],
        "viewMode": "categorized"
      }},
      "hidden": false
    }}
  ]
}}

Resume Text:
\"\"\"
{raw_text}
\"\"\"

Return only valid JSON.
"""

    try:
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

        content = response.choices[0].message.content.strip()

        # Parse string to dict safely
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}
# Unified parser
def parse_resume(filename: str, content: bytes) -> dict:
    raw_text = extract_text_from_resume(filename, content)
    structured_data = transform_text_to_resume_data(raw_text)
    return structured_data
