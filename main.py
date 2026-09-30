from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.chemist_user_handlers import router as chemist_user_router
from api.sabatier_material_handlers import router as sabatier_material_router
from data.sabatier_minio import ensure_material_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_material_bucket()
    yield


app = FastAPI(title="Sabatier Methane Synthesis API", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(sabatier_material_router)
app.include_router(chemist_user_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
