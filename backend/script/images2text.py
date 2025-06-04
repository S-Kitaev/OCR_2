import shutil
import os
import easyocr

def images_to_text(image_dir, text_file):

    reader = easyocr.Reader(
        ['ru', 'en'],
        model_storage_directory='backend/script/models',
        download_enabled=False,
    )

    files = sorted(os.listdir(image_dir))  # чтобы страницы были по порядку

    with open(text_file, 'w', encoding='utf-8') as f:
        for idx, file_name in enumerate(files, start=1):
            file_path = os.path.join(image_dir, file_name)

            if os.path.isfile(file_path):
                result = reader.readtext(file_path, detail=0, paragraph=True)

                f.write(f"\n||===========================================================||\n")
                f.write(f"||                      Страница {idx}                          ||\n")
                f.write(f"||===========================================================|| \n\n\n")
                f.write("\n".join(result))
                f.write("\n\n")

    shutil.rmtree(image_dir)
    print(f"Готово! Расшифровка сохранена в {text_file}")

