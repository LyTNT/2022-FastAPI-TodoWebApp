import sys
sys.path.append("..")
"""Trong routers folder luôn phải thêm line này đầu tiên"""

from fastapi import APIRouter, Depends,Request
import models
from db_postgre import engine, SessionLocal
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session


from fastapi import Form
from starlette import status
from starlette.responses import RedirectResponse
from .auth2 import get_current_user
# router= APIRouter()
#todo: add tags and prefixes in our responses to our routers
router = APIRouter(
    prefix="/todo",
    tags=["todo DB"],
    responses={401: {"user": "Not authorized"}}
)

models.Base.metadata.create_all(bind=engine)
templates= Jinja2Templates(directory="template")



def get_db(): #Du co access db session dc hay ko, thi cung close de do lai
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

"""REFERENCE
@router.get('/test-api-html')
async def test_api_html(request: Request):
    return templates.TemplateResponse("home.html",{"request":request})


@router.get('/')
async def read_all(db: Session= Depends(get_db)):
    return db.query(models.Todos).all()
"""

#todo: display the todo based on that specific user
@router.get("/", response_class=HTMLResponse)
async def read_all_by_user(request: Request,
                           db: Session = Depends(get_db)):
    # todos = db.query(models.Todos).filter(models.Todos.owner_id == 1).all()
    user= await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    todos = db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()

    return templates.TemplateResponse("home.html", {"request": request, "todo_boss":todos, "user": user})

@router.get("/edit_todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int,
                    db: Session = Depends(get_db)):
    # todo= db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    return templates.TemplateResponse("edit-todo.html", {"request": request,
                                                         "todo_para": todo, "user": user})

"""Nhap http://127.0.0.1:8000/todo/edit-todo/1
"""
@router.post("/edit_todo/{todo_id}", response_class=HTMLResponse)
async def save_edit_todo(request: Request, todo_id:int, title: str=Form(...), description: str=Form(...),
                      priority: int=Form(...),db: Session = Depends(get_db) ):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todo_model.title=title
    todo_model.description = description
    todo_model.priority = priority

    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todo", status_code=status.HTTP_302_FOUND)


"""Call the same API route, nhung different request"""
@router.get("/add_todo", response_class=HTMLResponse)
async def add_new_todo(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})
"""Sai một ly đi một dặm
lưu ý đối tượng TemplateResponse của router này là home.html"""
@router.post("/add_todo", response_class=HTMLResponse)
async def create_todo(request: Request, title: str=Form(...), description: str=Form(...),
                      priority: int=Form(...),db: Session = Depends(get_db) ):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    todo_model= models.Todos()
    todo_model.title=title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.complete = False
    # todo_model.owner_id = 1
    todo_model.owner_id= user.get("id")

    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todo", status_code=status.HTTP_302_FOUND)
"""chuyển hướng tới API router, THÊM /todo sai web address)
 /todo đó là tag
 http://127.0.0.1:8000/todo/"""

@router.get('/delete/{todo_id}')
async def delete_todo(request: Request, todo_id: int,
                db: Session= Depends(get_db)):
    ## kiem tra da login chua
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    ##2, kiểm tra xem có todo_id va user ko

    todo_model = db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .filter(models.Todos.owner_id==1).first()
    if todo_model is None:
        return RedirectResponse(url="/todo", status_code=status.HTTP_302_FOUND)
    ## sau do, tiến hành xoá
    db.query(models.Todos) \
        .filter(models.Todos.id == todo_id).delete()
    ## way2
    # db.delete(todo_model)
    db.commit() #save update status
    return RedirectResponse(url="/todo", status_code=status.HTTP_302_FOUND)
"""Hello Jamie,

That is correct. Http Request Methods support Delete. 
HTML forms and pages do not have a delete support, 
so you must handle everything through GET or POST.

Thanks,
Eric"""
@router.get('/complete/{todo_id}')
async def complete_todo(request: Request, todo_id: int,
                db: Session= Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todo.complete = not todo.complete #để tụi nó đảo chiều nhau
    db.add(todo) # chỉ có delete là ko có dòng này, còn PUT và POST thì có
    db.commit()
    return RedirectResponse(url="/todo", status_code=status.HTTP_302_FOUND)



