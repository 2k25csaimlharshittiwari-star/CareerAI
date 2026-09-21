from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.database import init_db
from app.config import ALLOWED_ORIGINS, APP_ENV
from app.routers.auth import router as auth_router
from app.routers.students import router as student_router

init_db()
app = FastAPI(title='CareerAI', version='3.0.0', description='AI-powered student career intelligence platform')
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=True, allow_methods=['GET','POST','PATCH','DELETE','OPTIONS'], allow_headers=['*'])
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware('http')
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if APP_ENV == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.get('/health', tags=['System'])
def health():
    return {'status':'ok','environment':APP_ENV,'service':'careerai'}

app.include_router(auth_router, prefix='/api')
app.include_router(student_router, prefix='/api')
FRONTEND = Path(__file__).resolve().parent.parent / 'frontend'
app.mount('/', StaticFiles(directory=str(FRONTEND), html=True), name='frontend')
