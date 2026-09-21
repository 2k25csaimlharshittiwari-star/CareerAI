import os
import uvicorn

if __name__ == '__main__':
    env = os.getenv('CAREERAI_ENV', 'development')
    uvicorn.run('app.main:app', host='0.0.0.0' if env == 'production' else '127.0.0.1', port=int(os.getenv('PORT','8000')), reload=env != 'production')
