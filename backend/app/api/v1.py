import json
from pathlib import Path

from backend.app.api import radar
from backend.app.core.config import get_settings
from backend.app.core.permissions import allowed, is_private_layer
from backend.app.core.security import authenticate, issue_session, read_session, revoke_session
from backend.app.services.radar_catalog import layer_catalog, observation_series
from backend.app.services.synthetic_area import area_summary, enabled, source_record
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[3]
SPEC = json.loads((ROOT / 'docs/contracts/openapi.yaml').read_text(encoding='utf-8'))

class Login(BaseModel):
    username: str
    password: str

def error(code: str, message: str, status: int, request: Request) -> JSONResponse:
    response = JSONResponse({'error': {'code': code, 'message': message,
                                        'request_id': request.state.request_id, 'details': []},
                             'synthetic': get_settings().demo_synthetic}, status_code=status)
    response.headers['Cache-Control'] = 'private, no-store'
    return response

def current(request: Request):
    return read_session(request.cookies.get('civisar_session'))

def scope_from_request(request: Request, path: str) -> str | None:
    return request.path_params.get('area_id') or request.query_params.get('area_id')

def authorize(request: Request, role: str, path: str):
    session = current(request)
    identity = session[0] if session else None
    if role != 'public' and identity is None:
        return error('UNAUTHENTICATED', 'Sign in required.', 401, request)
    if path.startswith('/layers') and 'layer_id' in request.path_params and is_private_layer(request.path_params['layer_id']):
        if identity is None:
            return error('UNAUTHENTICATED', 'Sign in required.', 401, request)
        role = 'analyst+'
    if not allowed(identity, role, scope_from_request(request, path)):
        return error('FORBIDDEN', 'Your role cannot access this resource.', 403, request)
    if (request.method in ('POST', 'PATCH', 'DELETE') and not (path == '/session' and request.method == 'POST')
            and (not session or request.headers.get('X-CSRF-Token') != session[1])):
        return error('FORBIDDEN', 'CSRF check failed.', 403, request)
    return None

def attach_routes(app: FastAPI) -> None:
    # Every draft operation is registered; only the small set below has real scaffold behavior.
    for path, methods in SPEC['paths'].items():
        for method, op in methods.items():
            role = op['x-required-roles']
            method_name = method.upper()
            async def handler(request: Request, _path=path, _method=method_name, _role=role):
                if _path == '/session' and _method == 'POST':
                    try:
                        data = Login.model_validate(await request.json())
                    except (ValueError, json.JSONDecodeError):
                        return error('INVALID_REQUEST', 'Invalid login request.', 422, request)
                    identity = authenticate(data.username, data.password)
                    if identity is None:
                        return error('UNAUTHENTICATED', 'Invalid credentials.', 401, request)
                    token, csrf = issue_session(identity)
                    response = JSONResponse({'synthetic': True, 'user_id': identity.user_id,
                        'role': identity.role, 'area_scopes': list(identity.area_scopes), 'csrf_token': csrf})
                    response.set_cookie('civisar_session', token, httponly=True,
                        secure=get_settings().cookie_secure, samesite='lax', max_age=28800)
                    response.headers['Cache-Control'] = 'private, no-store'
                    return response
                denial = authorize(request, _role, _path)
                if denial:
                    return denial
                if _path == '/session' and _method == 'DELETE':
                    revoke_session(request.cookies.get('civisar_session'))
                    response = Response(status_code=204)
                    response.delete_cookie('civisar_session')
                    return response
                if _path == '/health':
                    return {'status': 'ok', 'synthetic': get_settings().demo_synthetic}
                if not enabled():
                    session = current(request)
                    real = radar.handle(request, _path, session[0] if session else None, error)
                    if real is not None:
                        return real
                if _path == '/status':
                    return {'synthetic': True, 'sources': [], 'message': 'No live sources configured'}
                if _path == '/public/map':
                    return {'synthetic': True, 'resolution': 8, 'layers': [], 'suppressed': True,
                            'release_policy': '72h_and_review'}
                if _path == '/session' and _method == 'GET':
                    identity, csrf = current(request)
                    return {'synthetic': True, 'user_id': identity.user_id, 'role': identity.role,
                            'area_scopes': list(identity.area_scopes), 'csrf_token': csrf}
                if _path == '/roles':
                    identity, _ = current(request)
                    return {'synthetic': True, 'role': identity.role,
                            'area_scopes': list(identity.area_scopes)}
                if _path == '/sources':
                    if not enabled():
                        return error('UNAVAILABLE', 'No approved source catalogue is loaded.', 503, request)
                    return {'synthetic': True, 'items': [source_record('demo-source-01')],
                            'next_cursor': None}
                if _path == '/sources/{source_id}':
                    if not enabled():
                        return error('UNAVAILABLE', 'No approved source catalogue is loaded.', 503, request)
                    source = source_record(request.path_params['source_id'])
                    return source if source is not None else error(
                        'NOT_FOUND', 'Source not found.', 404, request)
                if _path == '/areas/{area_id}/summary':
                    if not enabled():
                        return error('UNAVAILABLE', 'No approved area result is loaded.', 503, request)
                    summary = area_summary(request.path_params['area_id'])
                    return summary if summary is not None else error(
                        'NOT_FOUND', 'Area not found.', 404, request)
                if _path == '/layers':
                    if not enabled():
                        return error('UNAVAILABLE', 'No approved layer catalogue is loaded.', 503, request)
                    return {'synthetic': True, 'items': layer_catalog(), 'next_cursor': None}
                if _path == '/layers/{layer_id}/timeseries':
                    if not enabled():
                        return error('UNAVAILABLE', 'No approved observation catalogue is loaded.', 503, request)
                    series = observation_series(request.path_params['layer_id'],
                                                request.query_params.get('area_id'))
                    return series if series is not None else error(
                        'NOT_FOUND', 'Observation series not found.', 404, request)
                if (_path.startswith('/layers/') and 'layer_id' in request.path_params
                        and request.path_params['layer_id'] == 'public-safe-demo'):
                    return error('NOT_FOUND', 'No published layer is available.', 404, request)
                return error('NOT_IMPLEMENTED', 'This operation is not implemented in the scaffold.', 501, request)
            app.add_api_route('/api/v1' + path, handler, methods=[method.upper()],
                name=op['operationId'], include_in_schema=False)
