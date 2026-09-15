from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
from api.sabatier_handlers import router as sabatier_router

app = FastAPI(title="Sabatier Methane Synthesis App")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(sabatier_router)

@app.get("/")
async def redirect_to_materials():
    return RedirectResponse(url="/sabatier_materials")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
