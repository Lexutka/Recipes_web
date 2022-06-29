from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Text, String, Boolean, Date, Identity, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime


engine = create_engine(
        'postgresql+psycopg2://igkyezeo:nrzV9tYWcAMR2mHBPEfGWBP5li0osjsL@abul.db.elephantsql.com/igkyezeo')
Session = sessionmaker(engine)
session = Session()

base = declarative_base()


class User(base):
    __tablename__ = 'users'
    id = Column(Integer, Identity(), primary_key=True)
    name = Column(String, UniqueConstraint(), nullable=False, unique=True)
    password = Column(Text, nullable=False)
    blocked_status = Column(Boolean, nullable=False, default=False)
    registered_date = Column(Date, default=datetime.date.today())
    updated_on = Column(Date, default=datetime.date.today(), onupdate=datetime.date.today())
    recipes = relationship("Recipe")


class Recipe(base):
    __tablename__ = 'recipes'

    id = Column(Integer, Identity(), primary_key=True)
    author = Column(String, ForeignKey('users.name', ondelete='CASCADE'))
    creation_date = Column(Date, default=datetime.date.today())
    title = Column(String, nullable=False)


base.metadata.create_all(engine)
