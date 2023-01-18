# python -m uvicorn app.main:app --reload

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.models import mongodb
from app.models.book import BookModel

from app.book_scraper import NaverBookScraper

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

# app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # book = BookModel(keyword="파이썬", publisher="BJPublic",
    #                  price=1200, image="me.png")
    # print(await mongodb.engine.save(book))
    return templates.TemplateResponse("index.html", {"request": request, "title": "콜렉터 북북이"})


@app.get("/search", response_class=HTMLResponse)
async def root(request: Request, q: str):
    keyword = q

    if not keyword:
        context = {"request": request, "title": "콜렉터"}
        return templates.TemplateResponse("index.html", context)

    if await mongodb.engine.find_one(BookModel, BookModel.keyword == keyword):
        books = await mongodb.engine.find(BookModel, BookModel.keyword == keyword)
        return templates.TemplateResponse("index.html", {"request": request, "title": "콜렉터 북북이", "books": books})

    naver_book_scraper = NaverBookScraper()
    books = await naver_book_scraper.search(keyword, total_page=10)
    book_models = []
    for book in books:
        # print(book)
        book_model = BookModel(
            keyword=keyword,
            publisher=book["publisher"],
            price=book["discount"],
            image=book["image"],
        )
        # print(book_model)
        book_models.append(book_model)

    await mongodb.engine.save_all(book_models)

    return templates.TemplateResponse("index.html", {"request": request, "title": "콜렉터 북북이", "books": books})


@app.on_event("startup")
def on_app_start():
    mongodb.connect()


@app.on_event("shutdown")
async def op_app_shutdown():
    mongodb.close()
