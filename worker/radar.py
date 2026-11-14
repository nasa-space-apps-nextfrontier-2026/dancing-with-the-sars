from backend.app.agents import unavailable

from .interfaces import SceneManifest, validate_manifest


def discover_scenes(*, metadata_only: bool = True):
    if not metadata_only:
        raise NotImplementedError('Earthdata access is not implemented')
    return []

def process_gcov(before: SceneManifest, after: SceneManifest):
    validate_manifest(before); validate_manifest(after)
    if before.processing_version != after.processing_version:
        return unavailable('Damage')
    return unavailable('Damage')

def process_gslc(*args, **kwargs):
    raise NotImplementedError('GSLC processing requires scientific QA')

def process_gunw(*args, **kwargs):
    raise NotImplementedError('GUNW is conditional; no cross-gap product assumed')

def calculate_coherence(*args, **kwargs):
    raise NotImplementedError('Cross-gap coherence is high risk and unimplemented')

def export_cog(*args, **kwargs):
    raise NotImplementedError('No scientific raster has been produced')
