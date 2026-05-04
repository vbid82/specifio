from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.routers import auth, products, csv_import, projects, requests

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connection pool is created lazily by SQLAlchemy
    yield
    # Shutdown: dispose connection pool
    await engine.dispose()


app = FastAPI(
    title="Specifio API",
    version="0.1.0",
    description="Specification workflow platform for architectural surfaces",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


app.include_router(auth.router)
app.include_router(products.router)
app.include_router(csv_import.router)
app.include_router(projects.router)
app.include_router(requests.router)

# Route registration — uncomment as modules are built
# from app.routes import products, specifiers, projects, samples, quotes, admin
# app.include_router(products.router, prefix="/api/products", tags=["products"])
# app.include_router(specifiers.router, prefix="/api/specifiers", tags=["specifiers"])
# app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
# app.include_router(samples.router, prefix="/api/samples", tags=["samples"])
# app.include_router(quotes.router, prefix="/api/quotes", tags=["quotes"])
# app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
