#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>


class PackageError(Exception):
    """Base class for errors related to packaging."""


class PackageSourceValidationError(PackageError):
    """Raised when package source files are invalid or fail validation."""


class PackageBuildError(PackageError):
    """Raised when a package fails to build correctly."""
