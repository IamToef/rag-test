import pytesseract
from PIL import Image
import docx
import io

def extract_images_from_docx(docx_path):
    """
    Trích text từ ảnh trong file docx
    """
    doc = docx.Document(docx_path)
    texts = []
    for rel in doc.part._rels.values():
        if "image" in rel.reltype:
            img_bytes = rel.target_part.blob
            img = Image.open(io.BytesIO(img_bytes))
            text = pytesseract.image_to_string(img, lang="vie")
            if text.strip():
                texts.append(text.strip())
    return texts
