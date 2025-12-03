"""
PDF Text Extraction Script
Extracts text from PDF files and saves as .txt
"""

import PyPDF2
import os
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file"""
    text_content = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"📄 Processing: {os.path.basename(pdf_path)}")
            print(f"   Pages: {num_pages}")
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if text.strip():
                    text_content.append(f"--- Page {page_num + 1} ---\n{text}\n")
            
            return "\n".join(text_content)
    
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {e}")
        return None


def process_pdf_folder(data_folder="data"):
    """Process all PDF files in data folder"""
    data_path = Path(data_folder)
    pdf_files = list(data_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in {data_folder}/")
        return
    
    print(f"\n🔍 Found {len(pdf_files)} PDF file(s)")
    print("=" * 60)
    
    for pdf_file in pdf_files:
        # Extract text
        text_content = extract_text_from_pdf(pdf_file)
        
        if text_content:
            # Save as .txt with same name
            txt_file = pdf_file.with_suffix('.txt')
            
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            print(f"✅ Saved: {txt_file.name}")
            print(f"   Characters: {len(text_content):,}")
        
        print()
    
    print("=" * 60)
    print("✅ PDF extraction complete!")


if __name__ == "__main__":
    process_pdf_folder()
