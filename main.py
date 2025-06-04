import os
import datetime
from backend.script.images2text import images_to_text
from backend.script.pdf2images import pdf_to_images

def main():
    image_dir = "backend/script/temp/img"
    pdf_path = input("Введите путь к PDF-файлу: ").strip()
    start = datetime.datetime.now()
    if not os.path.exists(pdf_path):
        print("Файл не найден.")
        return
    pdf_to_images(pdf_path, image_dir)
    images_to_text(image_dir, text_file='text.txt')
    end = datetime.datetime.now()
    print("Время выполнения программы: ",end - start)

if __name__ == "__main__":
    main()