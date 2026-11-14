from backend.app.policy.scope import area_in_scope

from .security import Identity

ROLE_LEVEL = {'analyst': 1, 'officer': 2, 'coordinator': 3, 'admin': 4}
PRIVATE_PREFIXES = ('/routes', '/closures', '/shelters', '/briefs', '/values', '/admin')

def required_level(role: str) -> int:
    return {'public': 0, 'signed_in': 1, 'analyst+': 1, 'officer+': 2,
            'coordinator+': 3, 'admin': 4}.get(role, 4)

def allowed(identity: Identity | None, role: str, area_id: str | None = None) -> bool:
    if role != 'public' and identity is None:
        return False
    if identity is None:
        return role == 'public'
    if ROLE_LEVEL[identity.role] < required_level(role):
        return False
    return area_id is None or area_in_scope(area_id, identity.area_scopes)

def is_private_layer(layer_id: str) -> bool:
    return layer_id not in ('public-safe-demo',)

# Cumulative capabilities per role (doc 07 role matrix); always intersected with area scope.
_CAPS = {
    'analyst': ['view_damage', 'view_people', 'view_services', 'view_alerts', 'view_validation',
                'review_alerts', 'create_briefs', 'trace_values'],
    'officer': ['view_routes', 'report_closures'],
    'coordinator': ['confirm_closures', 'view_shelters', 'record_field_checks'],
    'admin': ['manage_roles', 'retry_jobs', 'view_audit'],
}

def capabilities(role: str) -> list[str]:
    level = ROLE_LEVEL.get(role, 0)
    return [cap for r, caps in _CAPS.items() if ROLE_LEVEL[r] <= level for cap in caps]
