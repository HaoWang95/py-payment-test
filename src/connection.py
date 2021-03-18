from typing import List
from databases import Database
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql://ALAN:123456@127.0.0.1:5432/test"

db_instance = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = sqlalchemy.create_engine(DATABASE_URL)

LocalSession = sqlalchemy.orm.sessionmaker(autocommit= False, autoflush= False, bind=engine)

Base = declarative_base()

