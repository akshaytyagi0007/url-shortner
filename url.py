import model
from model import Url
from database import engine, SessionLocal
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from pydantic import BaseModel
import random
import string
from sqlalchemy.exc import IntegrityError
from fastapi.responses import RedirectResponse
model.Base.metadata.create_all(bind=engine)
app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UrlRequest(BaseModel):
    url : str


def url_shortner():
    shortUrl = ''.join(random.choices(string.ascii_lowercase+string.digits, k=5))
    return shortUrl


def get_string(shortUrl:str):
    if len(shortUrl)>5:
        digits = shortUrl[:-5]
        return digits
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invalid url")


db_dependency = Annotated[Session, Depends(get_db)]
@app.get("/all")
def get_all(db:db_dependency):
    result =  db.query(Url).all()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such Url Found")
    return result


@app.get("/{url}")
def get_url(db: db_dependency, url:str):
    get_id = get_string(url)
    result = db.query(Url).filter(
        Url.id == int(get_id),
        Url.shrt == url
    ).first()

    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such Url Found")
    return RedirectResponse(result.url)


@app.post("/createurl")
def create_url(db:db_dependency, new_Url_Request: UrlRequest):
    if new_Url_Request.url.startswith("https://") or new_Url_Request.url.startswith("http://"):
        new_Url = Url(**new_Url_Request.model_dump())
    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Invalid URL")

    try: 
        db.add(new_Url)
        db.commit()
        db.refresh(new_Url)
        new_Url.shrt = f"{new_Url.id}{url_shortner()}"
        db.commit()
        db.refresh(new_Url)
        return {"short_url": f"http://localhost:8000/{new_Url.shrt}"} 
    except IntegrityError:
        db.rollback()
        existing = db.query(Url).filter(Url.url == new_Url_Request.url).first()
        return {"short_url": f"http://localhost:8000/{existing.shrt}"}
    
@app.delete("/delete/{url}")
def delete_url(db:db_dependency,url :str):
    code = url.removeprefix("http://localhost:8000/")
    url_id = int(get_string(code))
    result = db.query(Url).filter(Url.id==url_id).first()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    db.delete(result)
    db.commit()
