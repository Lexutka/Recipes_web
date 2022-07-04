import datetime
from typing import Optional, Union, Any
import bcrypt
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, Identity, UniqueConstraint
from sqlalchemy import create_engine, types, func, desc, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Query

from settings import db_url


class DbConnection:
    """Методы данного класса позволяют осуществлять CRUD-операциис БД."""

    def __init__(self):
        self.engine = create_engine(db_url)
        self.session = sessionmaker(self.engine, expire_on_commit=False)()

    def new_user(self, name: str, password: str) -> None:
        """Сохранение нового пользователя"""
        encrypted_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        encrypted_pw = encrypted_pw.decode('utf8')
        user = User(name=name, password=encrypted_pw)
        self.session.add(user)
        self.session.commit()

    def new_recipe(
            self, author: str, title: str, r_type: str, description: str,
            cooking_steps: str, photo: str, tags: str
            ) -> None:
        """Сохранение нового рецепта"""
        recipe = Recipe(
            author=author,
            title=title,
            r_type=r_type,
            description=description,
            cooking_steps=cooking_steps,
            photo=photo,
            tags=tags
            )
        self.session.add(recipe)
        self.session.commit()

    def get_object(
            self, model: Union['User', 'Recipe'],
            where: Union['User', 'Recipe', None] = None,
            equal_to: Any = None, not_equal_to: Any = None
            ) -> 'Query':
        """Получение Query-объекта(-ов) по запросу с простой фильтрацией"""
        with self.session as session:
            if not where:
                return session.query(model)
            elif equal_to is not None:
                return session.query(model).where(where == equal_to)
            elif not_equal_to is not None:
                return session.query(model).where(where != not_equal_to)

    def get_top_users(self) -> 'Query':
        """Получение топа 10-ти пользователей по кол-ву
         рецептов с подсчетом кол-ва рецептов у каждого

        """
        with self.session as session:
            subquery = session.query(Recipe.author, func.count('name').label('recipes')). \
                group_by(Recipe.author).subquery()
            main_query = session.query(User, subquery.c.recipes).where(User.blocked_status == False). \
                outerjoin(subquery, User.name == subquery.c.author).order_by(desc(subquery.c.recipes))
            top = main_query.where(subquery.c.recipes > 0).limit(10)
            return top

    def if_exists(
            self, model: Union['User', 'Recipe'],
            where: Union['User', 'Recipe', None] = None,
            equal_to: Any = None, not_equal_to: Any = None
            ) -> bool:
        """Проверка существования строки в БД."""
        with self.session as session:
            query = self.get_object(model, where, equal_to, not_equal_to)
            result = session.query(query.exists())
            return result.scalar()

    def update_recipe(
            self, to_update: dict, where: Optional['Recipe'] = None,
            equal_to: Any = None, not_equal_to: Any = None
            ) -> None:
        """Обновление данных существующих рецептов с фильтрацией."""
        with self.session as session:
            query = self.get_object(Recipe, where, equal_to, not_equal_to)
            query.update(to_update, synchronize_session=False)
            session.commit()

    def update_user(
            self, to_update: dict, where: Optional['User'] = None,
            equal_to: Any = None, not_equal_to: Any = None
            ) -> None:
        """Обновление данных существующих пользователей с фильтрацией."""
        with self.session as session:
            query = self.get_object(User, where, equal_to, not_equal_to)
            query.update(to_update, synchronize_session=False)
            session.commit()

    def filtered_recipe_search(
            self, search: Optional[str] = None, r_type: Optional[str] = None,
            with_photo: Optional[str] = None, sort_by: Optional[str] = None
            ) -> 'Query':
        """Получение Query-объекта(-ов), соответствующих заданным параметрам поиска."""
        with self.session as session:
            q = session.query(Recipe).where(Recipe.blocked == False)
            if search:
                q = q.filter(or_(
                    func.lower(Recipe.author).like(f'%{search}%'.lower()),
                    func.lower(Recipe.title).like(f'%{search}%'.lower()),
                    func.lower(Recipe.tags).like(f'%{search}%'.lower())
                    ))
            if with_photo:
                q = q.where(Recipe.photo != '')
            if r_type:
                q = q.where(Recipe.r_type == r_type)
            if sort_by == 'by_date':
                q = q.order_by(desc(Recipe.creation_date))
            elif sort_by == 'by_title':
                q = q.order_by(Recipe.title)
            else:
                q = q.order_by(desc(Recipe.creation_date))
            return q


dbconnection = DbConnection()
base = declarative_base()


def db_init() -> None:
    """Создание таблиц и полей при запуске сервера."""
    base.metadata.create_all(dbconnection.engine)


class User(base):
    """Шаблон для таблицы с пользователями."""
    __tablename__ = 'users'

    id = Column(Integer, Identity(), primary_key=True)
    name = Column(String, UniqueConstraint(), nullable=False, unique=True)
    password = Column(Text, nullable=False)
    blocked_status = Column(Boolean, nullable=False, default=False)
    registered_date = Column(Date, default=datetime.date.today())
    updated_on = Column(Date, default=datetime.date.today(), onupdate=datetime.date.today())
    recipes = relationship("Recipe")


class ChoiceType(types.TypeDecorator):
    """Декоратор для работы с полем r_types
    в таблице Recipes, содержащего типы блюд.

    """
    impl = types.String
    cache_ok = False

    def __init__(self, choices, **kwargs):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        return [k for k, v in self.choices.items() if v == value][0]

    def process_result_value(self, value, dialect):
        return self.choices[value]


class Recipe(base):
    """Шаблон для таблицы с рецептами."""
    __tablename__ = 'recipes'

    TYPES = {'салат', 'первое', 'второе', 'десерт', 'напиток', 'выпечка'}

    id = Column(Integer, Identity(), primary_key=True)
    author = Column(String, ForeignKey('users.name', ondelete='CASCADE'))
    creation_date = Column(Date, default=datetime.date.today())
    updated_on = Column(Date, default=datetime.date.today(), onupdate=datetime.date.today())
    title = Column(String, nullable=False)
    r_type = Column(ChoiceType({
        'салат': 'салат', 'первое': 'первое', 'второе': 'второе',
        'десерт': 'десерт', 'напиток': 'напиток', 'выпечка': 'выпечка'
        }))
    description = Column(String, default='без описания')
    cooking_steps = Column(Text, nullable=False)
    photo = Column(String)
    likes = Column(Integer, default=0)
    tags = Column(String)
    blocked = Column(Boolean, default=False)
