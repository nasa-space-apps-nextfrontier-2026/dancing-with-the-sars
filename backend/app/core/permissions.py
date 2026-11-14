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
    return not (area_id is not None and '*' not in identity.area_scopes
                and area_id not in identity.area_scopes)

def is_private_layer(layer_id: str) -> bool:
    return layer_id not in ('public-safe-demo',)
