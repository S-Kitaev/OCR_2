import cv2
import numpy as np
import fitz
import os

output_folder = "backend/script/cache/img"

def pdf_to_images(pdf_path):
    pdf_document = fitz.open(pdf_path)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        pix = page.get_pixmap(dpi=300)  # увеличение DPI сразу

        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

        if pix.n == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        image_path = os.path.join(output_folder, f"page_{page_number + 1}.png")
        cv2.imwrite(image_path, image)

    pdf_document.close()