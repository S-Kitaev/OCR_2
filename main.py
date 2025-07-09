# main.py
import asyncio
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from backend.recognizer import recognize

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend/css"), name="static")
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
    request: Request,
    zip_path: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    # старт лога
    logs.append(f"Запущена обработка: {zip_path}")
    # кладём вызов recognize в фон
    background_tasks.add_task(run_recognize, zip_path)
    # возвращаем ту же страницу — JS на ней откроет SSE
    return templates.TemplateResponse("form.html", {"request": request, "zip_path": zip_path})

@app.get("/logs")
async def get_logs():
    return EventSourceResponse(log_generator())

# обёртка, чтобы из фонового таска обновлять логи
def run_recognize(zip_path: str):
    try:
        # внутрь recognize передаём колбэк для логирования
        time_start = datetime.now()
        recognize(zip_path, log_callback=logs.append)
        time_end = datetime.now()
        logs.append(f"Обработка заняла {(time_end - time_start) / 60 } минут")
        logs.append("✔ Обработка завершена.")
    except Exception as e:
        logs.append(f"‼ Ошибка: {e}")
