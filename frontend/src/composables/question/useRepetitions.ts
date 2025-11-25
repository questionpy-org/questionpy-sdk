/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, type ComputedRef, toRaw } from 'vue'

import type { ElementPath, RepetitionElement } from '@/types'

import { useModel } from './elements'
import { createFormDataValues } from './formDataUtils'

/**
 * Provides management for form repetitions.
 *
 * @param pathPrefix The parent's path of the repetition element.
 * @param element The repetition element.
 * @returns An object with repetition count and management methods.
 */
function useRepetitions(pathPrefix: ElementPath, element: RepetitionElement): UseRepetitionsReturn {
    const model = useModel(pathPrefix, element)

    return {
        count: computed(() =>
            // Enforce initial/minimal repetition count
            Math.max(model.value?.length ?? 0, element.initial_repetitions, element.minimum_repetitions),
        ),

        add() {
            const rawOldValue = toRaw(model.value) ?? [] // Avoid nested proxy objects
            model.value = [...rawOldValue, createFormDataValues(element.elements)]
        },

        remove(idx: number): void {
            model.value?.splice(idx, 1)
        },
    }
}

interface UseRepetitionsReturn {
    /** Repetition count. */
    count: ComputedRef<number>

    /** Adds a new repetition. */
    add: () => void

    /**
     * Removes a repetition.
     *
     * @param idx The index of the repetition to remove.
     */
    remove: (idx: number) => void
}

export default useRepetitions
