import easyocr
import concurrent.futures
import cv2
from tqdm import tqdm
import numpy as np


def init_reader():
    return easyocr.Reader(
        ['ru', 'en'],
        model_storage_directory='models',
        download_enabled=False
    )


def recognize_box(cropped_image_bytes):
    image_array = cv2.imdecode(cropped_image_bytes, cv2.IMREAD_COLOR)
    reader = init_reader()
    try:
        result = reader.readtext(image_array, detail=0, paragraph=False)
        return '\n'.join(result)
    except Exception as e:
        return f'[Ошибка распознавания: {e}]'


def detect_and_recognize(image):
    reader = init_reader()
    detection_result = reader.detect(image, width_ths=0.7)

    if not detection_result or not detection_result[0]:
        return ["[Нет детекций]"]

    boxes = detection_result[0][0]
    cropped_images_bytes = []

    for box in boxes:
        try:
            # Убедимся, что box — массив точек
            box = np.array(box)
            if box.ndim != 2 or box.shape[1] != 2:
                continue

            x_min = int(np.min(box[:, 0]))
            x_max = int(np.max(box[:, 0]))
            y_min = int(np.min(box[:, 1]))
            y_max = int(np.max(box[:, 1]))

            cropped = image[y_min:y_max, x_min:x_max]
            success, encoded = cv2.imencode('.png', cropped)
            if success:
                cropped_images_bytes.append(encoded)
        except Exception as e:
            print(f"Ошибка при обработке box: {e}")
            continue

    texts = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for result in tqdm(executor.map(recognize_box, cropped_images_bytes), total=len(cropped_images_bytes), desc='Распознавание рамок'):
            texts.append(result)

    return texts