from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.chemist_user_handlers import router as chemist_user_router
from api.sabatier_material_handlers import router as sabatier_material_router
from data.sabatier_minio import ensure_material_bucket

API_DESCRIPTION = """
Веб-сервис заявочной системы по теме «Синтез метана по реакции Сабатье».
Услуги системы — материалы реакции, то есть исходные вещества для синтеза метана.

**Авторизация.** Метод аутентификации проверяет логин и пароль по таблице
пользователей и сохраняет сессию в Redis, а её идентификатор отдаёт браузеру
в куке `session_id`. Каждый защищённый метод берёт эту куку, находит по ней
сессию в Redis и получает ид пользователя: нет сессии — `401`,
чужой материал — `403`.

**Права.** Без аутентификации доступно только чтение данных: список материалов
и лента. Методы создателя — добавление, публикация, удаление, лайк
и получение черновика — требуют действующей сессии. Создатель материала
подставляется автоматически из сессии, с клиента его передать нельзя.
"""

API_TAGS = [
    {
        "name": "Материалы реакции",
        "description": "Услуги системы: список с фильтром, лента, черновик, добавление, "
                       "публикация, удаление и лайк.",
    },
    {
        "name": "Инженеры-технологи",
        "description": "Пользователи системы: регистрация, аутентификация с сессией "
                       "в Redis и деавторизация.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_material_bucket()
    yield


app = FastAPI(
    title="Sabatier Methane Synthesis API",
    description=API_DESCRIPTION,
    version="4.0",
    openapi_tags=API_TAGS,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(sabatier_material_router)
app.include_router(chemist_user_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
