import shutil, os, easyocr

custom_characters = (
    '«»№'
    '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    '!@#$%^&*()_+-=[]{};:,./?|`~ '
)

def images_to_text(image_dir, text_file, log_callback=print):
    log_callback(f"[images2text] Проверяю папку: {image_dir}")
    log_callback("Файлы в ней: " + ", ".join(os.listdir(image_dir)))
    log_callback("Перевод изображений в текст...")
    reader = easyocr.Reader(
        ['ru', 'en'],
        model_storage_directory='backend/script/models',
        download_enabled=False,
        gpu=True
    )

    files = sorted(os.listdir(image_dir))
    all_lines = []

    with open(text_file, 'w', encoding='utf-8') as f:
        for idx, fname in enumerate(files, 1):
            log_callback(f"Расшифровывается страница {idx}")
            path = os.path.join(image_dir, fname)
            if not os.path.isfile(path): continue

            result = reader.readtext(
                path,
                detail=0,
                allowlist=custom_characters,
                contrast_ths=0.05,
                text_threshold=0.4
            )

            # Записываем в .txt
            log_callback(f"Запись страницы {idx} в .txt")
            f.write(f"--- Страница {idx} ---\n")
            for line in result:
                f.write(line + "\n")
            f.write("\n")

            all_lines.extend(result)

    shutil.rmtree(image_dir)
    log_callback(f"[✓] Расшифровка изображений сохранена в {text_file}")

    # Возвращаем единый текст
    return "\n".join(all_lines)

