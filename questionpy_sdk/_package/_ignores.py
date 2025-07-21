from collections.abc import Callable
from pathlib import Path

from pathspec import GitIgnoreSpec, PathSpec

from questionpy_common.constants import DIST_DIR

_DEFAULT_IGNORES = f"""
    # General
    *.tmp
    *cache
    .DS_Store
    {DIST_DIR}

    # Python
    venv
    .venv
    __pycache__
    *.pyc

    # JS
    node_modules

    # IDE
    .idea
    *.iml
    .vscode

    # VCS
    .git
    .svn
    .hg
    .bzr
    .jj
"""


def create_ignore_spec(gitignore_folder: Path, additional_ignores: list[str]) -> PathSpec:
    """Combines the default and the given ignores into one [PathSpec][pathspec.PathSpec].

    The order of precedence is:
        1. additional ignores
        2. `.gitignore` file
        3. default ignores

    And since the order of the ignore patterns is important, later patterns overwrite earlier ones, we concatenate them
    in reverse order.

    Args:
        gitignore_folder: the path to the directory where a `.gitignore` may be found
        additional_ignores: additional ignore patterns
    """
    ignores = _DEFAULT_IGNORES

    gitignore_file = gitignore_folder / ".gitignore"
    if gitignore_file.exists():
        ignores += gitignore_file.read_text()

    ignores += "\n".join(additional_ignores)

    return GitIgnoreSpec.from_lines(ignores.splitlines())


def create_ignore_file_callable(gitignore_folder: Path, additional_ignores: list[str]) -> Callable[[Path], bool]:
    """Returns a callable that determines whether a file should be ignored.

    The order of precedence is:
        1. additional ignores
        2. `.gitignore` file
        3. default ignores

    And since the order of the ignore patterns is important, later patterns overwrite earlier ones, we concatenate them
    in reverse order.

    Args:
        gitignore_folder: the path to the directory where a `.gitignore` may be found
        additional_ignores: additional ignore patterns
    """
    spec = create_ignore_spec(gitignore_folder, additional_ignores)

    def ignore_file(path: Path) -> bool:
        return spec.match_file(path)

    return ignore_file
