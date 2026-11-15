import logging
import secrets

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .api.v1 import attach_routes
from .core.config import get_settings
from .db.migrations import check_database

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s %(message)s')
app = FastAPI(title='CIVISAR scaffold', version='0.1.0',
              description='Synthetic development scaffold; consult docs/contracts/openapi.yaml')
app.add_middleware(CORSMiddleware, allow_origins=[get_settings().allowed_origin],
                   allow_credentials=True, allow_methods=['GET','POST','PATCH','DELETE'],
                   allow_headers=['Content-Type','X-CSRF-Token'])

@app.middleware('http')
async def request_id(request: Request, call_next):
    request.state.request_id = secrets.token_hex(8)
    response = await call_next(request)
    response.headers['X-Request-ID'] = request.state.request_id
    response.headers['X-Content-Type-Options'] = 'nosniff'
    if request.url.path != '/api/v1/health':
        response.headers['Cache-Control'] = 'private, no-store'
    return response

attach_routes(app)


@app.get('/internal/ready', include_in_schema=False)
def ready():
    try:
        if check_database():
            return {'status': 'ready', 'database': 'postgis'}
    except SQLAlchemyError:
        pass
    return JSONResponse({'status': 'unavailable', 'database': 'unavailable'}, status_code=503)


@app.on_event('startup')
def warm_public_map_context() -> None:
    """With PUBLIC_REAL_DATA on, build the public /map/context bundle (limit=100) in the background
    so the first visitor does not wait for it. Failures are logged; the route then builds on demand."""
    settings = get_settings()
    if not (settings.public_real_data and not settings.demo_synthetic):
        return
    import threading

    from .api import radar
    from .api.v1 import PUBLIC_VIEWER

    def _warm() -> None:
        try:
            radar._cached_map_context(PUBLIC_VIEWER, None, 100)
            logging.getLogger(__name__).info('public /map/context warmed')
        except Exception:
            logging.getLogger(__name__).exception('public /map/context warm-up failed')

    threading.Thread(target=_warm, daemon=True).start()
