from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.recognizer import recognize

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend/css"), name="static")
templates = Jinja2Templates(directory="frontend/templates")


@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/process", response_class=HTMLResponse)
async def process_zip(request: Request, zip_path: str = Form(...)):
    # Выполняем обработку
    df = recognize(zip_path)

    # Передаем результаты в шаблон
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "zip_path": zip_path,
            "df": df
        }
    )
