from fastapi import FastAPI


def test_health_route_is_registered():
    from src.api import register_routers

    app = FastAPI()
    register_routers(app)

    paths = {route.path for route in app.routes}

    assert any(path.endswith("/health") for path in paths)
