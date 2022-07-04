import aiohttp_jinja2
import jinja2
from aiohttp import web
import aiohttp_session
from aiohttp_session import get_session
import aiohttp_debugtoolbar
from aiohttp_debugtoolbar import toolbar_middleware_factory

from settings import config, BASE_DIR
from app.recipes.routes import setup_routes
from app.recipes.models import db_init


def setup_config(application):
    """Настройка файла конфигурации."""
    application['config'] = config


def setup_external_libraries(application):
    """Настройка внешних библиотек."""
    aiohttp_jinja2.setup(
        application,
        loader=jinja2.FileSystemLoader(f'{BASE_DIR}/templates'),
        )


@web.middleware
async def middleware(request, handler):
    """Настройка middleware для пользовательских сессий."""
    session = await get_session(request)
    session.new == True
    resp = await handler(request)
    return resp


def setup_app(application):
    """Настройка сервера и БД перед запуском."""
    setup_config(application)
    setup_external_libraries(application)
    setup_routes(application)
    db_init()


app = web.Application(middlewares=[toolbar_middleware_factory])


if __name__ == '__main__':
    aiohttp_session.setup(app, aiohttp_session.SimpleCookieStorage())  # в production заменить на Redis (НЕБЕЗОПАСНО!!!)
    setup_app(app)
    aiohttp_debugtoolbar.setup(app)
    web.run_app(app, port=config['common']['port'], host=config['common']['host'])
