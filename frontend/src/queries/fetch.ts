/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { z } from 'zod'

import { serverErrorSchema } from '@/schema/error'
import { serverValidationErrorsSchema } from '@/schema/options'
import type { ServerValidationErrors } from '@/schema/options/types'

/**
 * Represents an error that occurs during a fetch operation.
 * Extends the built-in `Error` class to include HTTP status information.
 */
class FetchError extends Error {
    /** The HTTP status code of the response. */
    status: number
    /** The status text corresponding to the HTTP status code. */
    statusText: string
    /** An optional detailed description of the error. */
    details?: string

    /**
     * Creates a new `FetchError` instance.
     *
     * @param status The HTTP status code of the response.
     * @param statusText The status text corresponding to the HTTP status code.
     * @param message A human-readable error message.
     * @param details An optional detailed description of the error.
     */
    constructor(status: number, statusText: string, message: string, details?: string) {
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
        let details: string | undefined = undefined

        try {
            const errorObj = serverErrorSchema.parse(await response.json())
            message = errorObj.error
            details = errorObj.details
        } catch (err) {
            if (err instanceof Error) {
                console.error(err.stack)
            }
        }

        return new FetchError(response.status, response.statusText, message, details)
    }
}

/**
 * Performs a GET request to the specified API path and validates the response using a Zod schema.
 *
 * @param path The relative API endpoint path (e.g., `manifest` or `options`).
 * @param schema The Zod schema used to validate the response data.
 * @param params Optional query parameters.
 * @returns A promise that resolves to the validated data.
 * @throws {@link FetchError} If the response is not OK (status code outside the 200-299 range).
 */
async function get<T>(
    path: string,
    schema: z.ZodType<T>,
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
    try {
        return schema.parse(await response.json())
    } catch (err) {
        if (err instanceof Error) {
            console.error(err.stack)
        }
        throw err
    }
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
async function post(path: string, body?: string): Promise<ServerValidationErrors | undefined> {
    const response = await fetch(`/api/${path}`, { method: 'POST', body })
    if (response.status === 422) {
        try {
            return serverValidationErrorsSchema.parse(await response.json())
        } catch (err) {
            if (err instanceof Error) {
                console.error(err.stack)
            }
            throw err
        }
    } else if (!response.ok) {
        throw await FetchError.fromResponse(response)
    }
}

export { FetchError, get, post }
