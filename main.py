from fastapi import FastAPI
from app.ai_logic import routes as ai_routes
from app import config

# logger = get_logger(__name__)  # Example usage

app = FastAPI(title="Assistant Dispatcher", debug=config.DEBUG)

# Include AI-related routes under a prefix, e.g. /ai
app.include_router(ai_routes.router, prefix="/ai")

if __name__ == "__main__":
  import uvicorn
  uvicorn.run("main:app", host="127.0.0.1", port=config.PORT, reload=True)