/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { z } from 'zod'

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

    /**
     * Creates a new `FetchError` instance.
     *
     * @param status The HTTP status code of the response.
     * @param statusText The status text corresponding to the HTTP status code.
     * @param message A human-readable error message.
     */
    constructor(status: number, statusText: string, message: string) {
        super(message)
        this.status = status
        this.statusText = statusText
        this.name = 'FetchError'
    }
}

/**
 * Performs a GET request to the specified API path and validates the response using a Zod schema.
 *
 * @param path The relative API endpoint path (e.g., `manifest` or `options`).
 * @param schema The Zod schema used to validate the response data.
 * @returns A promise that resolves to the validated data.
 * @throws {@link FetchError} If the response is not OK (status code outside the 200-299 range).
 */
async function get<T>(path: string, schema: z.ZodType<T>): Promise<T> {
    const response = await fetch(`/api/${path}`)
    if (!response.ok) {
        throw new FetchError(response.status, response.statusText, 'Failed to fetch data')
    }
    return schema.parse(await response.json())
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
async function post(path: string, body: string): Promise<ServerValidationErrors | undefined> {
    const response = await fetch(`/api/${path}`, { method: 'POST', body })
    if (response.status === 422) {
        return serverValidationErrorsSchema.parse(await response.json())
    } else if (!response.ok) {
        throw new FetchError(response.status, response.statusText, 'Failed to post data')
    }
}

export { FetchError, get, post }
