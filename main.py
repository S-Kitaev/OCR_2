import asyncio
from fastapi import FastAPI, Request, BackgroundTasks, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.recognizer import recognize
import os
import shutil
from datetime import datetime
from pathlib import Path


app = FastAPI()

BASE = Path(__file__).resolve().parent
# Создаем папку для загрузок, если ее нет
UPLOAD_DIR = BASE / "files" / "zips"
RESULTS_DIR = BASE / "files" / "results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# общий буфер логов
logs: list[str] = []

async def log_generator():
    while True:
        if logs:
            msg = logs.pop(0)
            yield f"-- {msg}"
        await asyncio.sleep(0.1)

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/process", response_class=HTMLResponse)
async def process_zip(
    # request: Request,
    # zip_path: str = Form(...),
    zip_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    try:
        # Сохраняем файл и добавляем метку времени к названию
        current_datetime = datetime.now()
        unix_time = current_datetime.timestamp()
        unix_time_decode = datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H-%M-%S')
        split_filename = zip_file.filename.split('.')
        filename_without_zip = '.'.join(split_filename[:-1])
        filename_without_zip_with_time = filename_without_zip + '_' + unix_time_decode
        filename = filename_without_zip_with_time + '.' + split_filename[-1]

        file_location = os.path.join(UPLOAD_DIR, filename)
        # Безопасное сохранение файла
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(zip_file.file, buffer)

        # Логируем начало обработки
        logs.append(f"Файл {filename_without_zip}.zip успешно загружен")
        logs.append(f"Начало обработки архива...")

        # Создаем имя для результирующего файла
        result_filename = f"Результат обработки {filename_without_zip_with_time}.xlsx"
        result_path = os.path.join(RESULTS_DIR, result_filename)


        # кладём вызов recognize в фон
        background_tasks.add_task(run_recognize,
                                  file_location,
                                  result_path,
                                  filename_without_zip_with_time,
                                  unix_time_decode)
        return JSONResponse(
            content={"status": "success",
                     "filename": filename_without_zip_with_time,
                     "result_filename": result_filename},
            status_code=200
        )
    except Exception as e:
        logs.append(f"‼ Ошибка при загрузке файла: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

@app.get("/logs")
async def get_logs():
    return EventSourceResponse(log_generator())


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(RESULTS_DIR, filename)

    if not os.path.exists(file_path):
        return JSONResponse(
            content={"error": "Файл не найден"},
            status_code=404
        )

    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# обёртка, чтобы из фонового таска обновлять логи
def run_recognize(zip_path: str, result_path: str, filename_without_zip_with_time: str, time: str):
    try:
        # внутрь recognize передаём колбэк для логирования
        recognize(zip_path, result_path, filename_without_zip_with_time, time, log_callback=logs.append)
        logs.append("✔ Обработка завершена.")
    except Exception as e:
        logs.append(f"‼ Ошибка: {e}")



