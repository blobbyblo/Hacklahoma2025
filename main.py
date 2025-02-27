from fastapi import FastAPI
from app.ai_logic import routes as ai_routes
from app import config

# logger = get_logger(__name__)  # Example usage

app = FastAPI(title="Assistant Dispatcher", debug=config.DEBUG)

app.include_router(ai_routes.router, prefix="/ai")

if __name__ == "__main__":
  import uvicorn
  uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True)