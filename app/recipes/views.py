import aiohttp_jinja2
from .models import User, session as db
from sqlalchemy import exists
from aiohttp import web
from aiohttp_session import get_session
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
      current_user = 'Гость'
      session = await get_session(self.request)
      if session.get('id'):
         current_user = db.query(User.name).filter(User.id==session.get('id')).scalar()
      return aiohttp_jinja2.render_template('register.html', self.request, locals())


class Register(web.View):

   @aiohttp_jinja2.template("register.html")
   async def get(self):
      pass

   async def post(self):
      data = await self.request.post()
      user = data.get('name')
      if user in ['LexLex']:
         msg = {'error': 'Пользователь с таким именем уже существует'}
         return aiohttp_jinja2.render_template('register.html', self.request, locals())
      else:
         password = bcrypt.hashpw(data.get('password').encode(), bcrypt.gensalt())
         password = password.decode('utf8')
         new_user = User(name=data.get('name'), password=password)
         db.add(new_user)
         db.commit()
      return aiohttp_jinja2.render_template('home.html', self.request, locals())


class Login(web.View):

   @aiohttp_jinja2.template("login.html")
   async def get(self):
      pass

   async def post(self):
      data = await self.request.post()
      name = data.get('name')
      try_password = data.get('password')
      if not db.query(exists().where(User.name==name)):
         msg = {'error_code': 20003, 'error_msg': 'User does not exists'}
         return aiohttp_jinja2.render_template('login.html', self.request, locals())
      user = db.query(User).filter(User.name==data.get('name')).first()
      if not bcrypt.checkpw(try_password.encode(), user.password.encode('utf8')):
         msg = {'error_code': 20004, 'error_msg': 'Password mismatch'}
         return aiohttp_jinja2.render_template('login.html', self.request, locals())
      user = db.query(User.id).filter(User.name==name).scalar()
      session = await get_session(self.request)
      session['id'] = user
      return web.Response(status=302, headers={'location': '/'})


class NewRecipe(web.View):

   @login_required
   @aiohttp_jinja2.template("new_recipe.html")
   async def get(self):
      author = db.get(User, 1).name
      types = ["салат", "первое", "второе", "десерт", "напиток", "выпечка"]
      data = {'types': types}
      return data

   async def post(self):
      #data = await self.request.post()
      pass
      #return web.Response(status=302, headers={'location': '/'})
