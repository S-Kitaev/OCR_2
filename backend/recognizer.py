import os
import zipfile
import datetime
import shutil
from backend.script.images2text import images_to_text
from backend.script.pdf2images import pdf_to_images


def recognize():
    # Запрашиваем путь к ZIP-архиву
    zip_path = input("Введите путь к ZIP-архиву: ").strip()
    start = datetime.datetime.now()

    if not os.path.exists(zip_path):
        print("ZIP-архив не найден.")
        return

    # Создаем временные рабочие папки
    temp_dir = "backend/script/temp"
    output_dir = "texts"

    # Очищаем/создаем рабочие директории
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Распаковываем архив
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Собираем все PDF-файлы
    pdf_files = []
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))

    # Обрабатываем каждый PDF-файл
    for pdf_path in pdf_files:
        file_name = os.path.basename(pdf_path)
        file_name = file_name[:-4]
        print(file_name)
        try:
            image_dir = os.path.join(temp_dir, f"images_{file_name}")
            os.makedirs(image_dir, exist_ok=True)

            output_text = os.path.join(output_dir, f"{file_name}.txt")
            pdf_to_images(pdf_path, image_dir)
            images_to_text(image_dir, output_text)
            shutil.rmtree(image_dir)

        except Exception as e:
            print("\n")

    # Удаляем временную директорию
    shutil.rmtree(temp_dir)

    end = datetime.datetime.now()
    print(f"\nОбработано файлов: {len(pdf_files)}")
    print(f"Время выполнения программы: {end - start}")
    print(f"Текстовые файлы сохранены в папку: {output_dir}")