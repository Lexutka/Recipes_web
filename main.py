import pathlib
import aiohttp_jinja2
import jinja2
import aiohttp_session
from aiohttp_session import get_session
from aiohttp import web
import aiohttp_debugtoolbar
from aiohttp_debugtoolbar import toolbar_middleware_factory
from app.recipes.routes import setup_routes


BASE_DIR = pathlib.Path(__file__).parent


def setup_external_libraries(application):
    aiohttp_jinja2.setup(
        application,
        loader=jinja2.FileSystemLoader(f"{BASE_DIR}/templates"),
        )


@web.middleware
async def middleware(request, handler):
    session = await get_session(request)
    session.new == True
    resp = await handler(request)
    print('произошел запрос')
    return resp


def setup_app(application):
    setup_external_libraries(application)
    setup_routes(application)


app = web.Application(middlewares=[toolbar_middleware_factory])


if __name__ == "__main__":
    aiohttp_session.setup(app, aiohttp_session.SimpleCookieStorage())  # в production заменить (НЕБЕЗОПАСНО!!!)
    setup_app(app)
    aiohttp_debugtoolbar.setup(app)
    web.run_app(app, port=8080, host="127.0.0.1")
