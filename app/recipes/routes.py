from app.recipes.views import Home, Register, Login, Logout, NewRecipe, Cabinet


def setup_routes(app):
    app.router.add_view("/", Home, name='home')
    app.router.add_view("/register", Register, name='register')
    app.router.add_view("/login", Login, name='login')
    app.router.add_view("/logout", Logout, name='logout')
    app.router.add_view("/new_recipe", NewRecipe, name='new-recipe')
    app.router.add_view("/cabinet", Cabinet, name='cabinet')
