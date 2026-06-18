from database import Base
from sqlalchemy import Column, Integer, String

class Url(Base):

    __tablename__ = "URL"
    id = Column(Integer, primary_key=True)
    url= Column(String, unique=True)
    shrt = Column(String)