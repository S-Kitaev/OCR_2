import os
import datetime
from backend.script.converter import process_images
from backend.script.pdf2images import pdf_to_images

def main():
    pdf_path = input("Введите путь к PDF-файлу: ").strip()
    start = datetime.datetime.now()
    if not os.path.exists(pdf_path):
        print("Файл не найден.")
        return
    pdf_to_images(pdf_path)
    process_images()
    end = datetime.datetime.now()
    print("Время выполнения программы: ",end - start)

if __name__ == "__main__":
    main()