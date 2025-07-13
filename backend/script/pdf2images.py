import cv2
import numpy as np
import fitz
import os
from pathlib import Path

def pdf_to_images(pdf_path, image_dir, log_callback=print):

    pdf_document = fitz.open(pdf_path)

    log_callback(f"[pdf2images] Рабочая папка: {Path.cwd()}")
    log_callback(f"[pdf2images] Пытаюсь создать: {image_dir}")
    image_dir = Path(image_dir).resolve()
    os.makedirs(image_dir, exist_ok=True)
    if not os.access(image_dir, os.W_OK):
        log_callback(f"‼ Нет прав на запись в {image_dir}")
        return

    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    for page_number in range(len(pdf_document)):
        log_callback(f"Обрабатывается страница PDF {page_number + 1} из {len(pdf_document)}")
        page = pdf_document.load_page(page_number)
        pix = page.get_pixmap(dpi=300)

        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

        if pix.n == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        image_path = os.path.join(image_dir, f"page_{page_number + 1}.png")

        # Сохранение с обработкой ошибок
        try:
            ok = cv2.imwrite(image_path, image)
            if ok:
                print(f"Сохранено: {image_path}")
            else:
                print(f"ОШИБКА: cv2.imwrite вернул False")

                # Альтернативное сохранение для диагностики
                try:
                    import PIL.Image
                    PIL.Image.fromarray(image).save(image_path)
                    print(f"Успешно сохранено через Pillow")
                except ImportError:
                    print("Pillow не установлен")
                except Exception as e:
                    print(f"Ошибка Pillow: {str(e)}")

        except cv2.error as e:
            print(f"ОШИБКА OpenCV: {str(e)}")
        except Exception as e:
            print(f"Общая ошибка: {str(e)}")

    log_callback("Изображения страниц созданы")

    pdf_document.close()