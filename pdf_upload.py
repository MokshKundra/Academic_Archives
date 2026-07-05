import pdfplumber
import base64
from pdf2image import convert_from_path
from providers.ext import ext_page

def image_to_b64(pg_img) -> str:
    import io
    buf = io.BytesIO()
    pg_img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def extractor(pdf_path : str, doc_title: str) -> str :
    with pdfplumber.open(pdf_path) as pdf:
        full_context = ""

        pages = pdf.pages
        images = convert_from_path(pdf_path, dpi=200, poppler_path= r"C:\poppler-26.02.0\Library\bin")

        print("--- doc converted ---")

        for i, (page, image) in enumerate(zip(pages, images)):

            print(f"--- on page {i} ---")

            extracted_text = page.extract_text()
            img_b64 = image_to_b64(image)

            response = ext_page(imgb64= img_b64, extracted_text= extracted_text)
            full_context += f"\n\n--- Page {i+1} --- (Doc Title:{doc_title} --- \n"
            full_context += response['message']['content']

        return full_context

# print(extractor(r"C:\Users\kundr\programming\Py_programming\slide-storage\Compre.pdf"))