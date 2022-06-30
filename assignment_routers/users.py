import sys
sys.path.append("..")
"""Trong routers folder luôn phải thêm line này đầu tiên"""

from .auth2 import get_current_user, get_user_exception, get_password_hash, authenticate_user
from .todo import function_http_exception, suscessful_response


from fastapi import  Depends, HTTPException,APIRouter
from sqlalchemy.orm import Session
import models #da tao module rieng
from db_postgre import engine, SessionLocal  ##da tao module rieng


router = APIRouter()
models.Base.metadata.create_all(bind=engine)

def get_db(): #Du co access db session dc hay ko, thi cung close de do lai
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

#todo: return all users within the application
@router.get('/')
async def read_all_user(db: Session= Depends(get_db)):
    return db.query(models.Users).all() #Users phải khớp tên tròn file model
#todo:  get a single user by a path parameter
"""Path para la tham so nam tren duong dan
Query para la tham so ko nam tren duong dan"""
@router.get('/{user_id}')
async def read_one_user(user_id: int,
                    db: Session = Depends(get_db)):
    if user_id is not None:

        user_model = db.query(models.Users)\
        .filter(models.Users.id == user_id)\
        .all()
        return user_model
    raise function_http_exception()
#todo: get a single user by a query parameter
#LUU Y: PHÁI CÓ '/' cuối đường dẫn nhá
@router.get('/one-user/')
async def read_one_user(user_id: int,
                    db: Session = Depends(get_db)):
    if user_id is not None:

        user_model = db.query(models.Users)\
        .filter(models.Users.id == user_id)\
        .all()
        return user_model
    raise function_http_exception()

#todo: modify their current user's password, if passed by authentication
#a
from passlib.context import CryptContext
#c
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7" # anything u want
ALGORITHM = "HS256"
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

#a
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#b
models.Base.metadata.create_all(bind=engine)

@router.put('/')
async def update_password_user(username: str, password: str,new_pass: str,
                      db: Session= Depends(get_db)):
    user = authenticate_user(username,password, db)
    if user is None:
        raise get_user_exception()
    user_model = db.query(models.Users) \
        .filter(models.Users.username == username).first()

    user_model.hashed_password = get_password_hash(new_pass)

    db.add(user_model)
    db.commit()
    return suscessful_response(201)
#todo: delete their own user.
@router.delete('/{user_id}')
def delete_todo(user_id: int,
                db: Session= Depends(get_db)):
    ##dau tien, kiểm tra xem có todo_id va user ko

    user_model = db.query(models.Users) \
        .filter(models.Users.id == user_id) \
        .first()
    if user_model is None:
        raise function_http_exception()  # da tao ham phia tren
    ## sau do, tiến hành xoá
    db.query(models.Users) \
        .filter(models.Users.id == user_id).delete()
    ## way2
    # db.delete(user_model)
    db.commit() #save update status
    return suscessful_response(201)
