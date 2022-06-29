import aiohttp_jinja2
from .models import session as db, User
from sqlalchemy import delete, select, exists
from aiohttp import web
from aiohttp_session import get_session
from aiohttp.web import RouteTableDef
import bcrypt

routes = RouteTableDef()

class Home(web.View):

   @aiohttp_jinja2.template("home.html")
   async def get(self):
      pass


class Register(web.View):

   @aiohttp_jinja2.template("register.html")
   async def get(self):
      pass

   async def post(self):
      data = await self.request.post()
      user = data.get('name') in db.query(User.name)
      if user:
         msg = {'error_code': 20001, 'error_msg': 'Это имя уже занято'}
      else:
         password = bcrypt.hashpw(data.get('password').encode(), bcrypt.gensalt())
         new_user = User(name=data.get('name'), password=password)
         db.add(new_user)
         db.commit()
         msg = {'error_code': 0, 'error_msg': 'ok'}
      return web.json_response(data=msg)


class Login(web.View):

   @aiohttp_jinja2.template("login.html")
   async def get(self):
      pass

   async def post(self):
      data = await self.request.post()
      name = data.get('name')
      try_password = data.get('password')
      if db.query(exists().where(User.name==name)):
         msg = {'error_code': 20003, 'error_msg': 'User does not exists'}
         return aiohttp_jinja2.render_template('login.html', self.request, locals())
      user = db.query(User).filter(User.name==data.get('name'))
      if not bcrypt.checkpw(try_password.password.encode(), user.password):
         msg = {'error_code': 20004, 'error_msg': 'Password mismatch'}
         return aiohttp_jinja2.render_template('login.html', self.request, locals())
      session = await get_session(self.request)
      session['uid'] = db.query(User).filter(User.name==data.get('name'))
      return web.Response(status=302, headers={'location': '/'})

