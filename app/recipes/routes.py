from app.recipes.views import Home, Register, Login


def setup_routes(app):
   app.router.add_view("/", Home, name='Home')
   app.router.add_view("/register", Register, name='Register')
   app.router.add_view("/login", Login, name='Login')
   #app.router.add_get("/new_recipe", )