from functools import wraps
import bcrypt
from aiohttp import web
from aiohttp.web import RouteTableDef
from aiohttp_jinja2 import render_template as render
from aiohttp_session import get_session, new_session

from settings import config
from .models import User, Recipe, dbconnection as db


token = config['admin']['token']  # Токен для доступа к режему администрирования

routes = RouteTableDef()


def login_required(func):
    """Проверяет, авторизирован ли пользователь.
    Если нет, отправляет на страницу авторизации.
    Админа отсылает на домашнюю страницу.

    """
    @wraps(func)
    async def inner(cls, *args, **kwargs):
        session = await get_session(cls.request)
        if 'id' not in session:
            return web.Response(status=302, headers={'location': '/login'})
        elif session['id'] == 'admin':  # админа нет в БД, поэтому он не может создавать рецепты
            return web.Response(status=302, headers={'location': '/'})
        else:
            return await func(cls, *args, **kwargs)

    return inner


def ban_check(func):
    """Проверяет, заблокирован ли пользователь.
    Если да, отправляет его в личный кабинет.

    """
    @wraps(func)
    async def inner(cls, *args, **kwargs):
        session = await get_session(cls.request)
        if 'id' not in session:
            return await func(cls, *args, **kwargs)
        elif session['id'] == 'admin':
            return await func(cls, *args, **kwargs)
        else:
            if db.get_object(model=User.blocked_status, where=User.id, equal_to=session['id']).scalar():
                return web.Response(status=302, headers={'location': '/cabinet'})
            else:
                return await func(cls, *args, **kwargs)

    return inner


class Home(web.View):
    """Обрабатывает домашнюю страницу.
    Отдает список рецептов, работает
    с поиском по ним.

    """
    @ban_check
    async def get(self):
        """Отдает список рецептов в соответствии с данными запроса."""
        # Вывод приветственной надписи с именем пользователя
        session = await get_session(self.request)
        if 'id' in session:
            if session['id'] == 'admin':
                current_user = 'Админ'
            else:
                current_user = db.get_object(model=User.name, where=User.id, equal_to=session['id']).scalar()
        else:
            current_user = 'Гость'

        # Фильтрация результатов согласно запросу
        req_data = self.request.rel_url.query
        try:
            search = req_data['search']
            if search == 'None':
                search = None
        except KeyError:
            search = None
        try:
            r_type = req_data['type_filter']
            if r_type == 'None':
                r_type = None
        except KeyError:
            r_type = None
        try:
            with_photo = req_data['with_photo']
            if with_photo == 'None':
                with_photo = None
        except KeyError:
            with_photo = None
        try:
            sort_by = req_data['sort_by']
            if sort_by == 'None':
                sort_by = None
        except KeyError:
            sort_by = None
        query = db.filtered_recipe_search(search=search, r_type=r_type, with_photo=with_photo, sort_by=sort_by)
        req_filt = {'search': search, 'type_filter': r_type, 'with_photo': with_photo, 'sort_by': sort_by}

        # Пагинация
        try:
            page = int(req_data['page'])
            prev = page - 1
        except KeyError:
            page = 1
            prev = None
        recipes_amount = query.count()
        if recipes_amount - page * 3 < 1:
            next = None
        else:
            next = page + 1
        entrypoint = (page - 1) * 3
        endpoint = entrypoint + 3
        results = query.slice(entrypoint, endpoint)

        status = 200
        if recipes_amount == 0:
            status = 400
        types = ["салат", "первое", "второе", "десерт", "напиток", "выпечка"]
        context = {'session': session,
                   'current_user': current_user,
                   'req_filt': req_filt,
                   'prev': prev,
                   'next': next,
                   'results': results,
                   'types': types}
        return render('home.html', self.request, context=context, status=status)


class Register(web.View):
    """Обрабатывает страницу регистрации.
    В случае успеха, пересылает на домашнюю страницу.
    После регистрации требуется авторизация.

    """
    async def get(self):
        session = await get_session(self.request)
        context = {'session': session}
        return render('register.html', self.request, locals())

    async def post(self):
        data = await self.request.post()
        name = data['name']
        if db.if_exists(model=User, where=User.name, equal_to=name):
            msg = 'Пользователь с таким именем уже существует'
            return render('register.html', self.request, locals(), status=400)
        else:
            db.new_user(name=data['name'], password=data['password'])
        return web.Response(status=302, headers={'location': '/'})


class Login(web.View):
    """Обрабатывает страницу авторизации.
    В случае успеха, пересылает на домашнюю страницу.

    """
    async def get(self):
        return render('login.html', self.request, locals())

    async def post(self):
        data = await self.request.post()
        name = data['name']
        try_password = data['password']
        if not db.if_exists(model=User, where=User.name, equal_to=name):
            msg = 'Пользователя с таким именем не существует'
            return render('login.html', self.request, locals(), status=400)
        user = db.get_object(model=User, where=User.name, equal_to=name).scalar()
        if not bcrypt.checkpw(try_password.encode(), user.password.encode('utf8')):
            msg = 'Неверный пароль'
            return render('login.html', self.request, locals(), status=400)
        session = await new_session(self.request)
        session['id'] = user.id
        return web.Response(status=302, headers={'location': '/'})


class Cabinet(web.View):
    """Отдает личные данные авторизованного пользователя.
    По запросу завершает текущую сессию и
    отправляет пользователя на домашнюю страницу.

    """
    @login_required
    async def get(self):
        session = await get_session(self.request)
        user = db.get_object(model=User, where=User.id, equal_to=session['id']).scalar()
        recipes_amount = db.get_object(model=Recipe, where=Recipe.author, equal_to=user.name).count()
        return render('cabinet.html', self.request, locals())

    async def post(self):
        session = await get_session(self.request)
        session.invalidate()
        return web.Response(status=302, headers={'location': '/'})


class Profile(web.View):
    """Отдает данные о пользователе.
    Адимн может его блокировать/разблокировать
    на этой странице

    """
    @ban_check
    async def get(self):
        session = await get_session(self.request)
        admin = False
        if 'id' in session:
            if session['id'] == 'admin':
                admin = True
        owner_name = self.request.rel_url.query['name']
        owner_profile = db.get_object(model=User, where=User.name, equal_to=owner_name).scalar()
        recipes_amount = db.get_object(model=Recipe, where=Recipe.author, equal_to=owner_name).count()
        context = {'session': session,
                   'admin': admin,
                   'owner_profile': owner_profile,
                   'recipes_amount': recipes_amount}
        try:
            test = owner_profile.id
        except AttributeError:
            return render('profile.html', self.request, context=context, status=404)
        return render('profile.html', self.request, context=context)

    @ban_check
    async def post(self):
        profile_name = self.request.rel_url.query['name']
        bl_unbl = None
        if db.get_object(model=User.blocked_status, where=User.name, equal_to=profile_name).scalar():
            bl_unbl = {'blocked_status': False}
        else:
            bl_unbl = {'blocked_status': True}
        db.update_user(where=User.name, equal_to=profile_name, to_update=bl_unbl)
        return web.Response(status=302, headers={'location': '/'})


class NewRecipe(web.View):
    """Обрабатывает запрос на создание нового рецепта."""
    @ban_check
    @login_required
    async def get(self):
        session = await get_session(self.request)
        author = db.get_object(model=User.name, where=User.id, equal_to=session['id']).scalar()
        types = ['салат', 'первое', 'второе', 'десерт', 'напиток', 'выпечка']
        context = {'session': session,
                   'author': author,
                   'types': types}
        return render('new_recipe.html', self.request, context=context)

    @ban_check
    async def post(self):
        data = await self.request.post()
        db.new_recipe(author=data['author'],
                      title=data['title'],
                      r_type=data['type'],
                      description=data['description'],
                      cooking_steps=data['cooking_steps'],
                      photo=data['photo'],
                      tags=data['tags'])
        return web.Response(status=302, headers={'location': '/'})


class RecipePage(web.View):
    """Отдает подробные данные о рецепте.
    Адимн может его блокировать/разблокировать
    на этой странице

    """
    @ban_check
    async def get(self):
        session = await get_session(self.request)
        if 'id' in session:
            admin = session['id'] == 'admin'
        recipe_id = self.request.rel_url.query['id']
        recipe = db.get_object(model=Recipe, where=Recipe.id, equal_to=recipe_id).scalar()
        try:
            test = recipe.id
        except AttributeError:
            return render('recipepage.html', self.request, locals(), status=404)
        return render('recipepage.html', self.request, locals())

    @ban_check
    async def post(self):
        rec_id = self.request.rel_url.query['id']
        bl_unbl = None
        if db.get_object(model=Recipe.blocked, where=Recipe.id, equal_to=rec_id).scalar():
            bl_unbl = {'blocked': False}
        else:
            bl_unbl = {'blocked': True}
        db.update_recipe(where=Recipe.id, equal_to=rec_id, to_update=bl_unbl)
        return web.Response(status=302, headers={'location': '/'})


class TopUsers(web.View):
    """Отдает данные о 10-ти пользователях,
    создавших наибольшее кол-во рецептов.

    """
    @ban_check
    async def get(self):
        session = await get_session(self.request)
        tops = db.get_top_users()
        return render('top_users.html', self.request, locals())


class Admin(web.View):
    """Позволяет перейти в режим администрирования
    (блокировка, разблокировка пользователей и рецептов)
    после ввода специального токена. Также позволяет
    по запросу выходить из данного режима.

    """
    async def get(self):
        session = await get_session(self.request)
        if 'id' in session:
            if session['id'] == 'admin':
                admin = True
        return render('admin.html', self.request, locals())

    async def post(self):
        data = await self.request.post()
        input_token = data['token']
        if input_token != token:
            msg = 'Неверный ключ'
            return render('admin.html', self.request, locals(), status=400)
        session = await new_session(self.request)
        session['id'] = 'admin'
        return web.Response(status=302, headers={'location': '/'})
