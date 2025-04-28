/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { z } from 'zod'

const serverErrorSchema = z
    .object({
        error: z.string().nonempty(),
        details: z.string().nonempty(),
    })
    .strict()

export { serverErrorSchema }
