import aiohttp_jinja2
import jinja2
from aiohttp import web

from app.settings import config, BASE_DIR


def setup_config(application):
   application["config"] = config


def setup_external_libraries(application):
   aiohttp_jinja2.setup(
      application,
      loader=jinja2.FileSystemLoader(f"{BASE_DIR}/templates"),
   )


# настроим url-пути для доступа к нашему будущему приложению
def setup_routes(application):
   from app.recipes.routes import setup_routes as setup_recipe_routes
   setup_recipe_routes(application)


def setup_app(application):
   setup_config(application)
   setup_external_libraries(application)
   setup_routes(application)


app = web.Application()


if __name__ == "__main__":
   setup_app(app)
   web.run_app(app, port=config["common"]["port"])

