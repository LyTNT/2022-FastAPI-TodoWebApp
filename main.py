
from fastapi import FastAPI, Depends
import models
from db_postgre import engine
from assignment_routers import auth2, todo

from starlette.staticfiles import StaticFiles
from starlette import status
from starlette.responses import RedirectResponse

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

"""mounting means adding a completely independent application to a specific path, it handle everything under the path, 
but the path operations declared in that sub application."""
app.mount("/static", StaticFiles(directory="static"), name="static")
"""DAY2"""
@app.get('/')
async def root():
    return RedirectResponse(url="/todo", status_code=status.HTTP_302_FOUND)

app.include_router(auth2.router)
app.include_router(todo.router)


