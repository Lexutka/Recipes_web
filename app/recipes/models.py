from sqlalchemy import create_engine, types
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, Identity, ForeignKey, UniqueConstraint
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


class ChoiceType(types.TypeDecorator):

    impl = types.String

    def __init__(self, choices, **kwargs):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        return [k for k, v in self.choices.items() if v == value][0]

    def process_result_value(self, value, dialect):
        return self.choices[value]


class Recipe(base):
    __tablename__ = 'recipes'

    TYPES = {'салат', 'первое', 'второе', 'десерт', 'напиток', 'выпечка'}

    id = Column(Integer, Identity(), primary_key=True)
    author = Column(String, ForeignKey('users.name', ondelete='CASCADE'))
    creation_date = Column(Date, default=datetime.date.today())
    updated_on = Column(Date, default=datetime.date.today(), onupdate=datetime.date.today())
    title = Column(String, nullable=False)
    type = Column(ChoiceType({"салат": "салат", "первое": "первое", "второе": "второе","десерт": "десерт", "напиток": "напиток", "выпечка": "выпечка"}))
    description = Column(String(80), default='без описания')
    cooking_steps = Column(Text, nullable=False)
    photo = Column(String)
    tags = Column(String)
    blocked = Column(Boolean, default=False)


base.metadata.create_all(engine)
