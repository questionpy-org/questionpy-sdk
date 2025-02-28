/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

/** Utility function to be used as exhaustion check. */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function assertNever(_: never): never {
    throw new Error('This code should never be reached')
}

/** Type guard for object. */
function isObject(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export { assertNever, isObject }
