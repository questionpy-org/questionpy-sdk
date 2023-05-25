from questionpy_common.manifest import Manifest


def create_normalized_filename(manifest: Manifest) -> str:
    """
    Creates a normalized file name for the given manifest.

    Args:
        manifest: manifest of the package

    Returns:
        normalized file name
    """
    return f"{manifest.namespace}-{manifest.short_name}-{manifest.version}.qpy"
