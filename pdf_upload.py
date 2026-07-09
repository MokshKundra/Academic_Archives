import pdfplumber
import base64
from config import settings
from pdf2image import convert_from_path
from providers.ext import ext_page


def needs_vision(page, extracted_text: str) -> bool:
    if not extracted_text or len(extracted_text.strip()) < 5:
        return True
    if len(page.images) > 0:
        return True
    return False 

def image_to_b64(pg_img) -> str:
    import io
    buf = io.BytesIO()
    pg_img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def extractor(pdf_path : str, doc_title: str, on_page_done = None) -> str :
    with pdfplumber.open(pdf_path) as pdf:
        full_context = ""
        poppler_path = settings.poppler_path

        print("--- doc processing started ---")

        pages = pdf.pages
        total_pages = len(pages)

        for i, page in enumerate(pages):
            print(f"--- on page {i + 1} ---")

            extracted_text = page.extract_text()
            
            if needs_vision(page, extracted_text):
                if poppler_path:
                    images = convert_from_path(
                        pdf_path, 
                        dpi=200, 
                        poppler_path=poppler_path, 
                        first_page=i+1, 
                        last_page=i+1
                    )
                else:
                    images = convert_from_path(
                        pdf_path, 
                        dpi=200, 
                        first_page=i+1, 
                        last_page=i+1
                    )
                
                image = images[0]
                img_b64 = image_to_b64(image)
                
                response = ext_page(imgb64=img_b64, extracted_text=extracted_text)
                page_content = response['message']['content']
            else:
                page_content = f"### EXTRACTED_TEXT\n{extracted_text}\n\n### VISUAL_ELEMENTS\nNONE"
            
            full_context += f"\n\n--- Page {i+1} --- (Doc Title:{doc_title} --- \n"
            full_context += page_content

            if on_page_done:
                on_page_done(i + 1, total_pages)

        return full_context