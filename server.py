import os

from app import app


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "3000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
