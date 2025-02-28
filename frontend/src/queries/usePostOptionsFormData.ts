/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineMutation } from '@pinia/colada'

import type { OptionsFormData } from '@/schema/options/types'

import { post } from './fetch'

/** Options form data mutation. */
const usePostOptionsFormData = defineMutation({
    mutation: async (formData: OptionsFormData) => (await post('options/state', JSON.stringify(formData))) ?? {},
})

export default usePostOptionsFormData
