import os.path
from collections.abc import Callable
from importlib.resources.abc import Traversable
from typing import TYPE_CHECKING

import jinja2

from questionpy_common.environment import Package, PackageNamespaceAndShortName, get_qpy_environment

if TYPE_CHECKING:
    from questionpy import Attempt, Question


class _CustomPrefixLoader(jinja2.PrefixLoader):
    """In contrast to the :class:`jinja2.PrefixLoader` this splits at the second occurrence of the delimiter.

    It enables us to handle paths like "@namespace/short_name/custom/path" with a prefix like "@namespace/short_name".
    """

    def get_prefix_and_name(self, template: str) -> tuple[str, str]:
        namespace, shortname, rest = template.split(self.delimiter, maxsplit=2)
        return namespace + self.delimiter + shortname, rest

    def get_loader(self, template: str) -> tuple[jinja2.BaseLoader, str]:
        try:
            prefix, name = self.get_prefix_and_name(template)
            loader = self.mapping[prefix]
        except (ValueError, KeyError) as e:
            raise jinja2.TemplateNotFound(template) from e
        return loader, name


class _TraversableTemplateLoader(jinja2.BaseLoader):
    """In contrast to the :class:`jinja2.FileSystemLoader` this does not support the auto-reload feature of jinja2."""

    def __init__(self, traversable: Traversable):
        self.traversable = traversable

    def get_source(self, environment: jinja2.Environment, template: str) -> tuple[str, str, Callable[[], bool] | None]:
        source_path = self.traversable.joinpath(template)
        try:
            return source_path.read_text("utf-8"), template, None
        except FileNotFoundError as e:
            raise jinja2.TemplateNotFound(template) from e


def _get_loader(package: Package) -> jinja2.BaseLoader | None:
    templates_directory = package.get_path("templates/")

    if not templates_directory.is_dir():
        # The package has no "templates" directory which would cause a template loader to raise an unhelpful ValueError.
        return None

    # Check whether the templates folder is inside a zip.
    if os.path.exists(str(templates_directory)):
        return jinja2.FileSystemLoader(str(templates_directory))
    return _TraversableTemplateLoader(templates_directory)


def create_jinja2_environment(attempt: "Attempt", question: "Question") -> jinja2.Environment:
    """Creates a Jinja2 environment with sensible default configuration.

    - Package templates are accessible under the prefix ``@<namespace>/<short_name>/``.
    - The prefix is optional when accessing templates of the current package.
    - The QPy environment, attempt, question and question type are available as globals.
    """
    qpy_env = get_qpy_environment()

    loader_mapping = {}
    for package in qpy_env.packages.values():
        loader = _get_loader(package)
        if loader:
            loader_mapping[f"@{package.manifest.namespace}/{package.manifest.short_name}"] = loader

    loaders: list[jinja2.BaseLoader] = [_CustomPrefixLoader(mapping=loader_mapping)]

    # Get caller package template loader.
    try:
        module_parts = attempt.__module__.split(".", maxsplit=2)
        namespace, short_name, *_ = module_parts
        key = PackageNamespaceAndShortName(namespace=namespace, short_name=short_name)
        package = qpy_env.packages[key]
    except (KeyError, ValueError) as e:
        msg = (
            "Current package namespace and shortname could not be determined from '__module__' attribute. Please do "
            "not modify the '__module__' attribute."
        )
        raise ValueError(msg) from e

    if current_package_loader := _get_loader(package):
        loaders.insert(0, current_package_loader)

    # Create a choice loader to handle template names without a prefix.
    choice_loader = jinja2.ChoiceLoader(loaders)

    env = jinja2.Environment(autoescape=True, loader=choice_loader)
    env.globals.update({
        "environment": qpy_env,
        "attempt": attempt,
        "question": question,
        "question_type": type(question),
    })

    return env
