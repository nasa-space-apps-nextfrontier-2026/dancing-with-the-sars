from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SceneManifest:
    collection_id: str
    acquisition_start: str
    processing_version: str
    track: int
    frame: int
    source_url: str | None = None

def compare_versions(before: SceneManifest, after: SceneManifest) -> bool:
    """True only if a future validated harmonization can be considered; never proof of comparability."""
    return before.processing_version == after.processing_version

def validate_manifest(scene: SceneManifest) -> None:
    if scene.track != 151 or scene.frame != 72 or not scene.collection_id:
        raise ValueError('Only the documented study track/frame is configured')
    if not scene.processing_version or not scene.acquisition_start:
        raise ValueError('Version and acquisition time are required')

def no_external_data(path: Path) -> bool:
    return path.exists() and path.is_file()
