from aiohttp_jinja2 import render_template as render
from .models import User, Recipe, dbconnection as db
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
           print()
           return await func(cls, *args, **kwargs)
        else:
           return web.Response(status=302, headers={'location': '/login'})
    return inner


class Home(web.View):

    async def get(self):
        session = await get_session(self.request)
        if session:
            current_user = db.get_object(model=User.name, where=User.id, equal_to=session['id']).scalar()
        else:
            current_user = 'Гость'
        recipes = db.get_object(model=Recipe, where=Recipe.blocked, equal_to=False).all()
        return render('home.html', self.request, locals())


class Register(web.View):

    async def get(self):
        session = await get_session(self.request)
        return render('register.html', self.request, locals())

    async def post(self):
        data = await self.request.post()
        name = data['name']
        if db.if_exists(model=User, where=User.name, equal_to=name):
           msg = {'error': 'Пользователь с таким именем уже существует'}
           return render('register.html', self.request, locals())
        else:
           db.new_user(name=data['name'], password=data['password'])
        return render('register.html', self.request, locals())


class Login(web.View):

    async def get(self):
        return render('login.html', self.request, locals())

    async def post(self):
        data = await self.request.post()
        name = data['name']
        try_password = data['password']
        if not db.if_exists(model=User, where=User.name, equal_to=name):
           msg = {'error_code': 20003, 'error_msg': 'Пользователя с таким именем не существует'}
           return render('login.html', self.request, locals())
        user = db.get_object(model=User, where=User.name, equal_to=name).scalar()
        if not bcrypt.checkpw(try_password.encode(), user.password.encode('utf8')):
            msg = {'error_code': 20004, 'error_msg': 'Неверный пароль'}
            return render('login.html', self.request, locals())
        session = await new_session(self.request)
        session['id'] = user.id
        return web.Response(status=302, headers={'location': '/'})


class Logout(web.View):

    @login_required
    async def get(self):
        session = await get_session(self.request)
        session.invalidate()
        return web.Response(status=302, headers={'location': '/'})


class Cabinet(web.View):

    @login_required
    async def get(self):
        session = await get_session(self.request)
        return render('cabinet.html', self.request, locals())


class Profile(web.View):

    async def get(self):
        session = await get_session(self.request)
        owner_name = self.request.rel_url.query['name']
        owner_profile = db.get_object(model=User, where=User.name, equal_to=owner_name).scalar()
        recipes_amount = db.get_object(model=Recipe, where=Recipe.author, equal_to=owner_name).count()
        return render('profile.html', self.request, locals())


class NewRecipe(web.View):

    @login_required
    async def get(self):
        session = await get_session(self.request)
        author = db.get_object(model=User.name, where=User.id, equal_to=session['id']).scalar()
        types = ["салат", "первое", "второе", "десерт", "напиток", "выпечка"]
        data = {'session': session, 'author': author, 'types': types}
        return render('new_recipe.html', self.request, locals())

    async def post(self):
        data = await self.request.post()
        db.new_recipe(author=data['author'],
            title=data['title'],
            type=data['type'],
            description=data['description'],
            cooking_steps=data['cooking_steps'],
            photo=data['photo'],
            tags=data['tags'])
        return web.Response(status=302, headers={'location': '/'})


class RecipePage(web.View):

    async def get(self):
        session = await get_session(self.request)
        recipe_id = self.request.rel_url.query['id']
        recipe = db.get_object(model=Recipe, where=Recipe.id, equal_to=recipe_id).scalar()
        return render('recipepage.html', self.request, locals())


class TopUsers(web.View):

    async def get(self):
        session = await get_session(self.request)
        users = db.get_top_users()
        return render('top_users.html', self.request, locals())