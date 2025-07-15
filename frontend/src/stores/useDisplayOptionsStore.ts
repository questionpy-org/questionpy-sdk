/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

import type { ClientQuestionDisplayOptions } from '@/types'

const DEFAULT_DISPLAY_OPTIONS = {
    general_feedback: true,
    specific_feedback: true,
    right_answer: true,
    correctness: true,
    roles: [],
}

/** Manages display options for attempts, persisted in the browser. */
const useDisplayOptionsStore = defineStore(
    'displayOptions',
    () => ({
        displayOptions: ref<ClientQuestionDisplayOptions>(DEFAULT_DISPLAY_OPTIONS),
    }),
    {
        // Persist data to localStorage
        persist: true,
    },
)

export default useDisplayOptionsStore
