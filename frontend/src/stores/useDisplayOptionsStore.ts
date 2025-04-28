/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

type Role = 'DEVELOPER' | 'PROCTOR' | 'SCORER' | 'TEACHER'

interface DisplayOptions {
    generalFeedback: boolean
    specificFeedback: boolean
    rightAnswer: boolean
    roles: Set<Role>
}

/** Provides attempt display options. */
const useDisplayOptionsStore = defineStore(
    'displayOptions',
    () => {
        const displayOptions = ref<DisplayOptions>({
            generalFeedback: true,
            specificFeedback: true,
            rightAnswer: true,
            roles: new Set(),
        })

        return {
            displayOptions,

            // Cache keys need to be serializable
            cacheKey: computed(() => ({
                ...displayOptions.value,
                roles: Array.from(displayOptions.value.roles),
            })),
        }
    },
    {
        // Persist data to localStorage
        persist: {
            // Convert Set to/from Array as JSON can't handle Sets
            serializer: {
                serialize: (state) =>
                    JSON.stringify({
                        displayOptions: {
                            ...state.displayOptions,
                            roles: Array.from(state.displayOptions.roles),
                        },
                    }),
                deserialize: (data) => {
                    const parsed = JSON.parse(data)
                    return {
                        displayOptions: {
                            ...parsed.displayOptions,
                            roles: new Set(parsed.displayOptions.roles),
                        },
                    }
                },
            },
        },
    },
)

export default useDisplayOptionsStore
export type { DisplayOptions }
