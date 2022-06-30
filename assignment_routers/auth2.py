import sys
sys.path.append("..")
from fastapi import Depends, HTTPException, status, Response,APIRouter, Form

from pydantic import BaseModel
from typing import Optional
import models
from sqlalchemy.orm import Session

#b
from db_postgre import SessionLocal, engine
#a
from passlib.context import CryptContext
#c
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
#d
from datetime import datetime, timedelta
from jose import jwt, JWTError

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from starlette.responses import RedirectResponse
#d

SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7" # anything u want
ALGORITHM = "HS256"

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

#a
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#b
models.Base.metadata.create_all(bind=engine)

templates= Jinja2Templates(directory="template")


#todo: add tags and prefixes in our responses to our routers
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Not authorized"}}
)
class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")
"""Muc đích class để lưu input thành path parameter"""
#b
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
#c
"""Chuyển đổi normal pass thành hashed_pass"""
def get_password_hash(password):
    return bcrypt_context.hash(password)
""" xac nhận rằng plain_pass va hashed_pass có phải the same hay ko"""
def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str, db):
    user = db.query(models.Users)\
        .filter(models.Users.username == username)\
        .first()

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False # kiểm tra password đc nhập vào, có khớp vs password chứa trong database
    return user
#d
def create_access_token(username: str, user_id: int,
                        expires_delta: Optional[timedelta] = None):

    encode = {"sub": username, "id": user_id}
    """Kiêm tra Thời gian, nếu expires_delta is not None"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM) # make real JWT token
"""DAY1
async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise get_user_exception()
        return {"username": username, "id": user_id}
    except JWTError:
        raise get_user_exception()
"""
"""DAY2"""
async def get_current_user(request: Request):
    try:
        token= request.cookies.get("access_token") #access_toke biến đã khai bên html rùi!
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            logout(request)
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=404, detail="Ko tim thay - Not found")

#d
# @router.post("/create_ver3/token2")
@router.post("/token")
async def login_for_access_token( response: Response,form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    """response: Response, cai thằng này mà khai phía cuối là ko đc"""
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        # raise token_exception()
        # raise False
        """De su dung alert minh chuyển qua return"""
        return False
    token_expires = timedelta(minutes=60)
    token = create_access_token(user.username,
                                user.id,
                                expires_delta=token_expires)
    response.set_cookie(key="access_token", value=token, httponly=True)
    # return {"token": token}
    return True
"""Result:
copy token hệ thống trả về, vào jwt.io
Token sẽ đc decoded/ giải mã ra thông tin mà bạn nhập"""
"""Muc đích hàm này là để decode"""
# @app.get("/create_ver3/token2") """Ham đc tạo ra nhưng chưa biết đc sử dung ntn"""
"""Hoá ra tạo ông này cho bên main.py"""


@router.get("/login", response_class=HTMLResponse) # nay gio chay ko dc do thieu response class
async def login_page(request: Request):
    return templates.TemplateResponse("login.html",{"request":request})

@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/todo", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(response=response, form_data=form, db=db)

        if not validate_user_cookie:
            msg = "Incorrect Username or Password"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        return response
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
"""LƯU Ý: CÁI THẰNG get và post luôn phải có path giống nhau,
 nếu ko action bên file html sẽ bị ảnh hưởng"""

@router.get("/logout")
async def logout(request: Request):
    msg = "Logout Successful"
    response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    response.delete_cookie(key="access_token")
    return response


@router.get('/register')
async def register_page(request: Request):
    return templates.TemplateResponse("register.html",{"request":request})

@router.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, email: str = Form(...), username: str = Form(...),
                        firstname: str = Form(...), lastname: str = Form(...),
                        password: str = Form(...), password2: str = Form(...),
                        db: Session = Depends(get_db)):

    validation1 = db.query(models.Users).filter(models.Users.username == username).first()

    validation2 = db.query(models.Users).filter(models.Users.email == email).first()

    if password != password2 or validation1 is not None or validation2 is not None:
        msg = "Invalid registration request"
        return templates.TemplateResponse("register.html", {"request": request, "msg": msg})

    user_model = models.Users()
    user_model.username = username
    user_model.email = email
    user_model.first_name = firstname
    user_model.last_name = lastname

    hash_password = get_password_hash(password)
    user_model.hashed_password = hash_password
    user_model.is_active = True

    db.add(user_model)
    db.commit()

    msg = "User successfully created"
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})