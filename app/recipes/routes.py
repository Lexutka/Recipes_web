from app.recipes.views import Home, Register, Login, Logout, NewRecipe, RecipePage, Cabinet, Profile, TopUsers


def setup_routes(app):
    app.router.add_view("/", Home, name='home')
    app.router.add_view("/register", Register, name='register')
    app.router.add_view("/login", Login, name='login')
    app.router.add_view("/logout", Logout, name='logout')
    app.router.add_view("/new_recipe", NewRecipe, name='new-recipe')
    app.router.add_view("/cabinet", Cabinet, name='cabinet')
    app.router.add_view("/profile/", Profile, name='profile')
    app.router.add_view("/recipe/", RecipePage, name='recipepage')
    app.router.add_view("/top-users", TopUsers, name='top-users')