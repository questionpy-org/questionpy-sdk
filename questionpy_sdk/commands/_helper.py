from questionpy_common.manifest import Manifest


def create_normalized_filename(manifest: Manifest) -> str:
    return f"{manifest.namespace}-{manifest.short_name}-{manifest.version}.qpy"
