import os, zipfile, datetime, shutil, glob, pandas as pd
from backend.script.pdf2images import pdf_to_images
from backend.script.images2text import images_to_text

def recognize():
    zip_path = input("Введите путь к ZIP-архиву: ").strip()
    if not os.path.exists(zip_path):
        print("ZIP-архив не найден."); return

    start = datetime.datetime.now()
    temp_dir = os.path.abspath("backend/script/temp")
    output_dir = os.path.abspath("texts")
    excel = os.path.abspath("Результат обработки.xlsx")

    # подготовка папок
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    pdf_files = glob.glob(os.path.join(temp_dir, '**', '*.pdf'), recursive=True)
    if not pdf_files:
        print("В ZIP-архиве не обнаружено ни одного PDF."); return

    print("Найденные PDF-файлы:", pdf_files)

    records = []  # будет список dict'ов {filename: ..., text: ...}

    for pdf_path in pdf_files:
        name = os.path.splitext(os.path.basename(pdf_path))[0]
        print(f"→ Обработка {name}...")
        try:
            image_dir = os.path.join(temp_dir, f"images_{name}")
            os.makedirs(image_dir, exist_ok=True)
            pdf_to_images(pdf_path, image_dir)
            text_file = os.path.join(output_dir, f"{name}.txt")
            full_text = images_to_text(image_dir, text_file)

            records.append({
                'filename': name,
                'text': full_text
            })

        except Exception as e:
            print(f"Ошибка при обработке {name}:", e)

    # Удаляем temp
    shutil.rmtree(temp_dir)

    # Строим DataFrame: каждая строка = файл, 2 колонки
    df = pd.DataFrame(records, columns=['filename', 'text'])
    df.to_excel(excel, index=False, sheet_name='Temporary')

    end = datetime.datetime.now()
    print(f"\nОбработано файлов: {len(records)}")
    print(f"Время выполнения: {end - start}")
    print(f"Текстовые файлы сохранены в папке: {output_dir}")