/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import type { DetailedServerError, EditableElement, FormElement, HasElements } from '.'

/** Utility function to be used as exhaustion check. */

function assertNever(value: never): never {
    throw new Error(`This code should never be reached. Value='${value}'`)
}

/** Type guard for `FormElement` with `elements` property. */
function hasElements(elem: FormElement): elem is HasElements {
    return Array.isArray((elem as HasElements).elements)
}

/** Type guard for `FormElement` that is editable. */
function isEditableElement(elem: FormElement): elem is EditableElement {
    return !['group', 'static_text', 'hidden', 'id'].includes(elem.kind)
}

/** Type guard for `object`. */
function isObject(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** Type guard for `DetailedServerError`. */
function isDetailedServerError(value: unknown): value is DetailedServerError {
    return (
        isObject(value) &&
        typeof value.error === 'string' &&
        (typeof value.details === 'string' || Array.isArray(value.details) || value.detail === null)
    )
}

export { assertNever, hasElements, isDetailedServerError, isEditableElement, isObject }
