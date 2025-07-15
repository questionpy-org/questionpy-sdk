/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

/**
 * Generates an 8-character URL-safe ID using 48 bits of randomness.
 *
 * @returns A short, unique ID string.
 */
function generateId(): string {
    const bytes = crypto.getRandomValues(new Uint8Array(6)) // 6 bytes = 48 bits
    return btoa(String.fromCharCode(...bytes))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '')
}

export { generateId }
