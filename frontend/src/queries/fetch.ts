/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { isDetailedServerError } from '@/types'
import type { DetailedServerError } from '@/types'

/**
 * Represents an error that occurs during a fetch operation.
 * Extends the built-in `Error` class to include HTTP status information.
 */
class FetchError extends Error {
    /** The HTTP status code of the response. */
    status: number
    /** The status text corresponding to the HTTP status code. */
    statusText: string
    /** Optional detailed error information, which may include a stack trace or validation errors. */
    details: DetailedServerError['details']

    /**
     * Creates a new `FetchError` instance.
     *
     * @param status The HTTP status code of the response.
     * @param statusText The status text corresponding to the HTTP status code.
     * @param message A human-readable error message.
     * @param details An optional detailed description of the error.
     */
    constructor(status: number, statusText: string, message: string, details: DetailedServerError['details']) {
        super(message)
        this.status = status
        this.statusText = statusText
        this.name = 'FetchError'
        this.details = details
    }

    /**
     * Creates a `FetchError` from a `Response` object.
     * Tries to parse the response body as JSON and extract `error` and `details`.
     *
     * @param response The Response object to create the error from.
     * @returns A Promise resolving to a FetchError instance.
     */
    static async fromResponse(response: Response): Promise<FetchError> {
        let message = `${response.status} ${response.statusText}`
        let details: DetailedServerError['details'] = null

        try {
            const serverError = await response.json()
            if (isDetailedServerError(serverError)) {
                message = serverError.error
                details = serverError.details
            }
        } catch {
            // Pass if JSON decode fails
        }

        return new FetchError(response.status, response.statusText, message, details)
    }
}

/**
 * Performs a GET request to the specified API endpoint.
 *
 * @param path The relative API endpoint path (e.g., `manifest` or `options`).
 * @param params Optional query parameters.
 * @template T The response data type.
 * @returns A promise that resolves to the validated data.
 * @throws {@link FetchError} If the response is not OK (status code outside the 200-299 range).
 */
async function get<T = unknown>(
    path: string,
    params?: Record<string, string | number | boolean | string[]>,
): Promise<T> {
    const url = new URL(`/api/${path}`, window.location.origin)

    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                value.forEach((v) => url.searchParams.append(key, v.toString()))
            } else {
                url.searchParams.append(key, value.toString())
            }
        })
    }

    const response = await fetch(url)
    if (!response.ok) {
        throw await FetchError.fromResponse(response)
    }

    return await response.json()
}

/**
 * Performs a POST request to the specified API path with the provided body.
 *
 * @param path The relative API endpoint path (e.g., `options/state`).
 * @param body The request body as a string (usually JSON).
 * @returns A promise that resolves to `ServerValidationErrors` if the response status is 422 (validation error),
 *          or `undefined` if the request is successful.
 * @throws {@link FetchError} If the response is not OK (status code outside the 200-299 range) and not 422.
 */
async function post<T = unknown>(path: string, body?: string): Promise<T | undefined> {
    const response = await fetch(`/api/${path}`, { method: 'POST', body })
    if (response.status === 422) {
        return await response.json()
    } else if (!response.ok) {
        throw await FetchError.fromResponse(response)
    }
}

/**
 * Performs a DELETE request to the specified API path.
 *
 * @param path The relative API endpoint path (e.g., `options/state`).
 * @returns
 * @throws {@link FetchError} If the response is not OK (status code outside the 200-299 range).
 */
async function delete_(path: string): Promise<undefined> {
    const response = await fetch(`/api/${path}`, { method: 'DELETE' })
    if (!response.ok) {
        throw await FetchError.fromResponse(response)
    }
}

export { delete_, FetchError, get, post }
