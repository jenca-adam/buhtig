from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine=create_engine=create_engine("sqlite:///models.db",echo=True,connect_args={"check_same_thread":False})
Base = declarative_base()
class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    uname=Column(String)
    fname=Column(String)
    lname=Column(String)
    email=Column(String)
    pw=Column(String)
    admin=Column(Boolean)
class Repo(Base):
    __tablename__='repo'
    id=Column(Integer,primary_key=True)
    owner=Column(Integer)
    name=Column(String)
    visible=Column(Boolean)
    allowed=Column(String)
Base.metadata.create_all(engine)
Session=sessionmaker(bind=engine)
session=Session()
def user_by_uname(un):
    return session.query(User).filter(User.uname==un)
def user_by_email(em):
    return session.query(User).filter(User.email==em)
