import shutil
import os
import easyocr

def process_images():
    folder = 'backend/script/cache/img'
    output_file = 'text.txt'
    reader = easyocr.Reader(['ru', 'en'], gpu=False, model_storage_directory='backend/script/models', download_enabled=False)

    if not os.path.exists(folder):
        print(f'Папка {folder} не найдена!')
        return

    files = sorted(os.listdir(folder))  # чтобы страницы были по порядку

    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, file_name in enumerate(files, start=1):
            file_path = os.path.join(folder, file_name)

            if os.path.isfile(file_path):
                result = reader.readtext(file_path, detail=0, paragraph=True)

                f.write(f"\n||===========================================================||\n")
                f.write(f"||                      Страница {idx}                          ||\n")
                f.write(f"||===========================================================|| \n\n\n")
                f.write("\n".join(result))
                f.write("\n\n")

    shutil.rmtree(folder)
    print(f"Готово! Расшифровка сохранена в {output_file}")
