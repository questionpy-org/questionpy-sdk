#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from questionpy_common.api.qtype import MigrationError, MigrationErrorKind
from questionpy_common.environment import Package

from ._base import MigrationQuestionStateWithVersion


class MigrationNotImplementedError(MigrationError):
    kind = MigrationErrorKind.NOT_IMPLEMENTED


class MigrationNotPossibleError(MigrationError):
    kind = MigrationErrorKind.NOT_POSSIBLE


class SpecificMigrationFailedError(MigrationError):
    def __init__(self, from_version: int, to_version: int, step: int):
        temporary = False
        msg = f"The migration at step {step} from state version {from_version} to state version {to_version} "

        if self.__cause__ and isinstance(self.__cause__, MigrationNotPossibleError):
            self.kind = MigrationErrorKind.NOT_POSSIBLE

            temporary = self.__cause__.temporary
            reason = f": {self.__cause__.reason}" if self.__cause__.reason else "."
            msg += f"is not possible{reason}"
        else:
            self.kind = MigrationErrorKind.FAILED
            msg += "failed."

        super().__init__(reason=msg, temporary=temporary)


class MigrationPackageMissmatchError(MigrationError):
    kind = MigrationErrorKind.PACKAGE_MISSMATCH

    def __init__(self, package: Package, state: MigrationQuestionStateWithVersion):
        msg = (
            f"The provided question state must origin from this package. "
            f"Expected @{package.manifest.namespace}/{package.manifest.short_name}, "
            f"got @{state.package_namespace}/{state.package_short_name}."
        )
        super().__init__(reason=msg)


class MigrationQuestionStateInvalidError(MigrationError):
    kind = MigrationErrorKind.QUESTION_STATE_INVALID


class MigrationFailedError(MigrationError):
    kind = MigrationErrorKind.FAILED


class MigrationDiscoveryError(MigrationError):
    """Discovering migrations is not possible."""

    kind = MigrationErrorKind.DISCOVERY_ERROR
