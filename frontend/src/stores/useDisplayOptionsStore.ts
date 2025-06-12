/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

import type { ClientQuestionDisplayOptions } from '@/types'

/** Provides attempt display options. */
const useDisplayOptionsStore = defineStore(
    'displayOptions',
    () => {
        const displayOptions = ref<ClientQuestionDisplayOptions>({
            general_feedback: true,
            specific_feedback: true,
            right_answer: true,
            roles: [],
        })

        return { displayOptions }
    },
    {
        // Persist data to localStorage
        persist: true,
    },
)

export default useDisplayOptionsStore
