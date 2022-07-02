import aiohttp_jinja2
from aiohttp_jinja2 import render_template as render
from .models import User, Recipe, session as db
from sqlalchemy import exists
from aiohttp import web
from aiohttp_session import get_session, new_session
from aiohttp.web import RouteTableDef
from functools import wraps
import bcrypt


routes = RouteTableDef()


def login_required(func):  # Проверка статуса входа пользователя
    """This function applies only to class views."""

    @wraps(func)
    async def inner(cls, *args, **kwargs):
        session = await get_session(cls.request)
        user_id = session.get("id")
        if user_id:
           print(db.query(User.id).filter(User.id==user_id).scalar())
           return await func(cls, *args, **kwargs)
        else:
           return web.Response(status=302, headers={'location': '/login'})
    return inner


class Home(web.View):

    @aiohttp_jinja2.template("home.html")
    async def get(self):
        session = await get_session(self.request)
        if session:
            current_user = db.query(User.name).filter(User.id==session['id']).scalar()
        else:
            current_user = 'Гость'
        recipes = db.query(Recipe).where(Recipe.blocked==False).all()
        return render('home.html', self.request, locals())


class Register(web.View):

    @aiohttp_jinja2.template("register.html")
    async def get(self):
        session = await get_session(self.request)
        return render('register.html', self.request, locals())

    async def post(self):
        data = await self.request.post()
        name = data['name']
        if db.query(exists().where(User.name==name)):
           msg = {'error': 'Пользователь с таким именем уже существует'}
           return render('register.html', self.request, locals())
        else:
           password = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt())
           password = password.decode('utf8')
           new_user = User(name=data['name'], password=password)
           db.add(new_user)
           db.commit()
        return render('register.html', self.request, locals())


class Login(web.View):

    @aiohttp_jinja2.template("login.html")
    async def get(self):
        pass

    async def post(self):
        data = await self.request.post()
        name = data['name']
        try_password = data['password']
        if not db.query(exists().where(User.name==name)):
           msg = {'error_code': 20003, 'error_msg': 'User does not exists'}
           return render('login.html', self.request, locals())
        user = db.query(User).filter(User.name==name).scalar()
        if not bcrypt.checkpw(try_password.encode(), user.password.encode('utf8')):
            msg = {'error_code': 20004, 'error_msg': 'Password mismatch'}
            return render('login.html', self.request, locals())
        user = db.query(User.id).filter(User.name==name).scalar()
        session = await new_session(self.request)
        session['id'] = user
        return web.Response(status=302, headers={'location': '/'})


class Logout(web.View):

    @login_required
    async def get(self):
        session = await get_session(self.request)
        session.invalidate()
        return web.Response(status=302, headers={'location': '/'})


class Cabinet(web.View):

    @login_required
    @aiohttp_jinja2.template("cabinet.html")
    async def get(self):
        session = await get_session(self.request)
        return render('cabinet.html', self.request, locals())


class NewRecipe(web.View):

    @login_required
    @aiohttp_jinja2.template("new_recipe.html")
    async def get(self):
        session = await get_session(self.request)
        author = db.query(User.name).where(User.id==session['id']).scalar()
        types = ["салат", "первое", "второе", "десерт", "напиток", "выпечка"]
        data = {'session': session, 'author': author, 'types': types}
        return data

    async def post(self):
        data = await self.request.post()
        new_recipe = Recipe(author=data['author'],
                            title=data['title'],
                            type=data['type'],
                            description=data['description'],
                            cooking_steps=data['cooking_steps'],
                            photo=data['photo'],
                            tags=data['tags'])
        db.add(new_recipe)
        db.commit()
        return web.Response(status=302, headers={'location': '/'})
