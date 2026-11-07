"""Render provenance shared by the CLI and Blender. No Blender dependency."""
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from core import content, digest
from native_materials import MATERIAL_VERSION


def image_digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def manifest_path(image):
    return Path(image).with_suffix('.render.json')


def record_render(image, scene, **settings):
    """Publish provenance only after Blender has successfully written the image."""
    image = Path(image)
    info = {**settings, 'schema': 'room-studio-render/1', 'material_version': MATERIAL_VERSION,
            'revision': scene['revision'], 'scene_hash': digest(content(scene)),
            'style': scene['style'], 'period': scene['period'],
            'environment': scene['environment'], 'image': image.name,
            'image_hash': image_digest(image),
            'created_utc': datetime.now(timezone.utc).isoformat()}
    path = manifest_path(image)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(info, f, indent=2, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return info


def render_status(scene, image):
    image = Path(image)
    path = manifest_path(image)
    base = {'current_revision': scene['revision'], 'current_material_version': MATERIAL_VERSION}
    if not image.is_file() or not path.is_file():
        return {**base, 'status': 'MISSING',
                'reason': 'image_missing' if not image.is_file() else 'provenance_missing'}
    try:
        info = json.loads(path.read_text())
        if (not isinstance(info, dict) or info.get('schema') != 'room-studio-render/1'
                or type(info.get('revision')) is not int
                or not all(isinstance(info.get(k), str) and len(info[k]) == 64
                           for k in ('scene_hash', 'image_hash'))):
            raise ValueError('Invalid render provenance')
        base.update(render_revision=info['revision'], room=info.get('room'),render_material_version=info.get('material_version'))
        if info['image_hash'] != image_digest(image):
            return {**base, 'status': 'STALE', 'reason': 'image_changed'}
        if info.get('material_version') != MATERIAL_VERSION:
            return {**base, 'status': 'STALE', 'reason': 'renderer_changed'}
        if info['scene_hash'] != digest(content(scene)):
            return {**base, 'status': 'STALE', 'reason': 'scene_changed'}
        return {**base, 'status': 'CURRENT', 'reason': 'content_matches'}
    except (ValueError, TypeError, OSError):
        return {**base, 'status': 'STALE', 'reason': 'provenance_invalid'}
