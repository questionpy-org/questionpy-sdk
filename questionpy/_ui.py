import importlib.resources
from typing import TYPE_CHECKING

import jinja2

from questionpy_common.environment import Package, get_qpy_environment

if TYPE_CHECKING:
    from questionpy import Attempt, Question


def _loader_for_package(package: Package) -> jinja2.BaseLoader | None:
    pkg_name = f"{package.manifest.namespace}.{package.manifest.short_name}"
    if not (importlib.resources.files(pkg_name) / "templates").is_dir():
        # The package has no "templates" directory, which would cause PackageLoader to raise an unhelpful ValueError.
        return None

    # TODO: This looks for templates in python/<namespace>/<short_name>/templates, we might want to support a different
    #  directory, such as resources/templates.
    return jinja2.PackageLoader(pkg_name)


def create_jinja2_environment(attempt: "Attempt", question: "Question") -> jinja2.Environment:
    """Creates a Jinja2 environment with sensible default configuration.

    - Library templates are accessible under the prefix ``qpy/``.
    - Package templates are accessible under the prefix ``<namespace>.<short_name>/``.
    - The QPy environment, attempt, question and question type are available as globals.
    """
    qpy_env = get_qpy_environment()

    loader_mapping = {}
    for package in qpy_env.packages.values():
        loader = _loader_for_package(package)
        if loader:
            loader_mapping[f"{package.manifest.namespace}.{package.manifest.short_name}"] = loader

    # Add a place for SDK-Templates, such as the one used by ComposedAttempt etc.
    loader_mapping["qpy"] = jinja2.PackageLoader(__package__)

    env = jinja2.Environment(autoescape=True, loader=jinja2.PrefixLoader(mapping=loader_mapping))
    env.globals.update({
        "environment": qpy_env,
        "attempt": attempt,
        "question": question,
        "question_type": type(question),
    })

    return env
