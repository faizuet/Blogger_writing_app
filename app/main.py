from fastapi import FastAPI
from app.Apis import auth, blog

app = FastAPI(title="Blogger Writing App")

# ---------- Routers ----------
app.include_router(auth.router)
app.include_router(blog.router)

