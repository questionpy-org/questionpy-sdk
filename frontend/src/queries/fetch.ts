/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { isDetailedServerError } from '@/types'
import { isServerValidationErrors } from '@/types/typeUtils'
import type { DetailedServerError, ServerValidationErrors } from '@/types'

const API_BASE = '/api/'

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
    constructor(
        status: number,
        statusText: string,
        message: string,
        details: DetailedServerError['details'] = undefined,
    ) {
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
     * @param response The `Response` object to create the error from.
     * @returns A Promise resolving to a `FetchError` instance.
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

/** Represents server-side form validation errors. */
class FormValidationError extends FetchError {
    /** Server validation errors. */
    validationErrors: ServerValidationErrors

    /**
     * Creates a new `FormValidationError` instance.
     *
     * @param status The HTTP status code of the response.
     * @param statusText The status text corresponding to the HTTP status code.
     * @param message A human-readable error message.
     * @param details An optional detailed description of the error.
     */
    constructor(status: number, statusText: string, message: string, validationErrors: ServerValidationErrors) {
        super(status, statusText, message)
        this.name = 'FormValidationError'
        this.validationErrors = validationErrors
    }

    /**
     * Creates a `FormValidationError` from a `Response` object with status '422 Unprocessable Content'.
     *
     * @param response The `Response` object to create the error from.
     * @returns A Promise resolving to a `FormValidationError` instance.
     */
    static async fromResponse(response: Response): Promise<FormValidationError> {
        if (response.status !== 422) {
            throw Error('Expected 422 Unprocessable Content')
        }

        const message = `${response.status} ${response.statusText}`

        const validationErrors = await response.json()
        if (isServerValidationErrors(validationErrors)) {
            return new FormValidationError(response.status, response.statusText, message, validationErrors)
        }

        throw Error('Failed to parse server validation errors')
    }
}

/**
 * Performs a GET request to the specified API endpoint.
 *
 * @param path The relative API endpoint path (e.g., `manifest` or `options`).
 * @param params Optional query parameters.
 * @template T The response data type.
 * @returns A promise that resolves to the response data type.
 * @throws {@link FetchError} If the response is not OK (status code outside the 200-299 range).
 */
async function get<T = unknown>(
    path: string,
    params?: Record<string, string | number | boolean | string[]>,
): Promise<T> {
    const url = new URL(`${API_BASE}${path}`, window.location.origin)

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
 * @template T The response data type.
 * @returns A promise that resolves to the response data type.
 * @throws {@link FetchError} If the response is not OK (status code outside the 200-299 range) and not 422.
 * @throws {@link FormValidationError} If the response status code is 422.
 */
async function post<T>(path: string, body?: string | FormData): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, { method: 'POST', body })
    if (response.ok) {
        return await response.json()
    } else if (response.status === 422) {
        // ServerValidationError
        throw await FormValidationError.fromResponse(response)
    }
    throw await FetchError.fromResponse(response)
}

/**
 * Performs a DELETE request to the specified API path.
 *
 * @param path The relative API endpoint path (e.g., `options/state`).
 * @throws {@link FetchError} If the response is not OK (status code outside the 200-299 range).
 */
async function delete_(path: string): Promise<undefined> {
    const response = await fetch(`${API_BASE}${path}`, { method: 'DELETE' })
    if (!response.ok) {
        throw await FetchError.fromResponse(response)
    }
}

export { API_BASE, delete_, FetchError, FormValidationError, get, post }
