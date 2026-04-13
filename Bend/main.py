from app.main_api import app
from app.config import APP_HOST, APP_PORT


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=APP_HOST, port=APP_PORT)

