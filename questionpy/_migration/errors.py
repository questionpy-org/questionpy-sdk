#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from questionpy_common.api.qtype import MigrationError, MigrationErrorKind
from questionpy_common.environment import Package

from ._base import MigrationQuestionStateWithVersion


class MigrationNotImplementedError(MigrationError):
    def __init__(self) -> None:
        super().__init__(kind=MigrationErrorKind.NOT_IMPLEMENTED)


class MigrationNotPossibleError(MigrationError):
    def __init__(self, *args: object, reason: str | None = None, temporary: bool = False) -> None:
        super().__init__(*args, kind=MigrationErrorKind.NOT_POSSIBLE, reason=reason, temporary=temporary)


class SpecificMigrationFailedError(MigrationError):
    def __init__(self, cause: Exception, from_version: int, to_version: int, step: int):
        temporary = False
        msg = f"The migration at step {step} from state version {from_version} to state version {to_version} "

        if isinstance(cause, MigrationNotPossibleError):
            kind = MigrationErrorKind.NOT_POSSIBLE

            temporary = cause.temporary
            reason = f": {cause}" if cause.reason else "."
            msg += f"is not possible{reason}"
        else:
            kind = MigrationErrorKind.FAILED
            msg += "failed."

        super().__init__(kind=kind, reason=msg, temporary=temporary)


class MigrationPackageMissmatchError(MigrationError):
    def __init__(self, package: Package, state: MigrationQuestionStateWithVersion):
        msg = (
            f"The provided question state must origin from this package. "
            f"Expected @{package.manifest.namespace}/{package.manifest.short_name}, "
            f"got @{state.package_namespace}/{state.package_short_name}."
        )

        super().__init__(kind=MigrationErrorKind.PACKAGE_MISSMATCH, reason=msg)


class MigrationPackageVersionMissmatchError(MigrationError):
    def __init__(self, expected_state_version: int, actual_state_version: int):
        msg = (
            f"The provided question state must have the same state version used by this package. Expected "
            f"'{expected_state_version}', got '{actual_state_version}."
        )

        super().__init__(kind=MigrationErrorKind.PACKAGE_MISSMATCH, reason=msg)


class MigrationQuestionStateInvalidError(MigrationError):
    def __init__(self) -> None:
        super().__init__(kind=MigrationErrorKind.QUESTION_STATE_INVALID)


class MigrationFailedError(MigrationError):
    def __init__(self) -> None:
        super().__init__(kind=MigrationErrorKind.FAILED)


class MigrationDiscoveryError(MigrationError):
    def __init__(self) -> None:
        super().__init__(kind=MigrationErrorKind.DISCOVERY_ERROR)
