import os
import zipfile
import datetime
import shutil
import glob
import pandas as pd
from backend.script.pdf2images import pdf_to_images
from backend.script.images2text import images_to_text
from pathlib import Path

def recognize(zip_path: str, log_callback=print):
    if not os.path.exists(zip_path):
        log_callback("ZIP-архив не найден."); return

    start = datetime.datetime.now()
    from pathlib import Path
    BASE = Path(__file__).resolve().parent.parent

    temp_dir = BASE / "backend" / "script" / "temp"
    output_dir = BASE / "texts"
    excel = BASE / "Результат обработки.xlsx"

    # подготовка папок
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    pdf_files = glob.glob(os.path.join(temp_dir, '**', '*.pdf'), recursive=True)
    if not pdf_files:
        log_callback("В ZIP-архиве не обнаружено ни одного PDF."); return

    pdf_names = []
    for pdf in pdf_files:
        pdf_name = os.path.basename(pdf)
        pdf_names.append(pdf_name)

    pdf_files_string = "\n".join(pdf_names)

    log_callback(f"Найденные PDF-файлы: \n{pdf_files_string}")

    records = []  # будет список dict'ов {filename: ..., text: ...}

    for pdf_path in pdf_files:
        name = os.path.splitext(os.path.basename(pdf_path))[0]
        log_callback(f"\n Обработка {name}...")
        try:
            image_dir = os.path.join(temp_dir, f"images_{name}")
            os.makedirs(image_dir, exist_ok=True)
            pdf_to_images(pdf_path, image_dir, log_callback=log_callback)
            text_file = os.path.join(output_dir, f"{name}.txt")
            full_text = images_to_text(image_dir, text_file, log_callback=log_callback)

            records.append({
                'filename': name,
                'text': full_text
            })

        except Exception as e:
            log_callback(f"Ошибка при обработке {name}: {e}")

    # Удаляем temp
    shutil.rmtree(temp_dir)

    # Строим DataFrame: каждая строка = файл, 2 колонки
    df = pd.DataFrame(records, columns=['filename', 'text'])
    df.to_excel(excel, index=False, sheet_name='Temporary')

    end = datetime.datetime.now()
    log_callback(f"\nОбработано файлов: {len(records)}")
    log_callback(f"Время выполнения: {end - start}")
    log_callback(f"Текстовые файлы сохранены в папке: {output_dir}")
    log_callback(f"Excel сохранен в: {excel}")

    return df