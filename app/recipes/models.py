from sqlalchemy import create_engine, types, func
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, Identity, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import bcrypt


class DbConnection:

    def __init__(self):
        self._engine = create_engine('postgresql+psycopg2://igkyezeo:nrzV9tYWcAMR2mHBPEfGWBP5li0osjsL@abul.db.elephantsql.com/igkyezeo')
        self._session = sessionmaker(self._engine, expire_on_commit=False)()

    def new_user(self, name, password):
        encrypted_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        encrypted_pw = encrypted_pw.decode('utf8')
        user = User(name=name, password=encrypted_pw)
        self._session.add(user)
        self._session.commit()
        return user

    def new_recipe(self, author, title, type, description, cooking_steps, photo, tags):
        recipe = Recipe(author=author,
            title=title,
            type=type,
            description=description,
            cooking_steps=cooking_steps,
            photo=photo,
            tags=tags)
        self._session.add(recipe)
        self._session.commit()
        return recipe

    def get_object(self, model, where=None, equal_to=None, not_equal_to=None):
        with self._session as session:
            if not where:
                return session.query(model)
            elif equal_to != None:
                return session.query(model).where(where==equal_to)
            elif not_equal_to != None:
                return session.query(model).where(where!=not_equal_to)

    def get_top_users(self):
        with self._session as session:
            subquery = session.query(Recipe.author, func.count('name').label('recipes')).\
                group_by(Recipe.author).subquery()
            main_query = session.query(User, subquery.c.recipes).where(User.blocked_status==False).\
                outerjoin(subquery, User.name == subquery.c.author).order_by(subquery.c.recipes)
            top = main_query.limit(10)
            return top

    def if_exists(self, model, where, equal_to=None, not_equal_to=None):
        with self._session as session:
            query = self.get_object(model, where, equal_to, not_equal_to)
            result = session.query(query.exists())
            return result.scalar()


dbconnection = DbConnection()
base = declarative_base()
base.metadata.create_all(dbconnection._engine)


class User(base):
    __tablename__ = 'users'
    id = Column(Integer, Identity(), primary_key=True)
    name = Column(String, UniqueConstraint(), nullable=False, unique=True)
    password = Column(Text, nullable=False)
    blocked_status = Column(Boolean, nullable=False, default=False)
    registered_date = Column(Date, default=datetime.date.today())
    updated_on = Column(Date, default=datetime.date.today(), onupdate=datetime.date.today())
    recipes = relationship("Recipe")

    def __str__(self):
        recipes_amount = len(self.recipes)
        return str(recipes_amount)


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
    description = Column(String, default='без описания')
    cooking_steps = Column(Text, nullable=False)
    photo = Column(String)
    tags = Column(String)
    blocked = Column(Boolean, default=False)


