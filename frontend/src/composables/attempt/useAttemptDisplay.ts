/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, toValue } from 'vue'
import type { ComputedRef, MaybeRef } from 'vue'

import { assertNever, type AttemptData } from '@/types'

/**
 * Returns reactive display values derived from an attempt object.
 *
 * @param attemptData A ref or raw value containing attempt data.
 * @returns Reactive properties including formatted score, human-readable status, and scoring state.
 */
function useAttemptDisplay(attemptDataRef: MaybeRef<AttemptData | undefined>): UseAttemptDisplayReturn {
    const attemptData = computed(() => toValue(attemptDataRef))
    const isScored = computed(() => typeof attemptData.value?.scoring_code === 'string')

    return {
        displayScore: computed(() => (isScored.value ? attemptData.value?.score?.toFixed(1) : undefined)),
        displayStatus: computed(() => {
            const attemptStatusCode = attemptData.value?.attempt_status
            switch (attemptStatusCode) {
                case 'IN_PROGRESS':
                    return 'In progress'
                case 'SCORED':
                    return 'Scored'
                case 'STARTED':
                    return 'Started'
                case undefined:
                    return ''
                default:
                    return assertNever(attemptStatusCode)
            }
        }),
        isScored,
    }
}

interface UseAttemptDisplayReturn {
    /** Pretty representation of the attempt status. */
    displayStatus: ComputedRef<string>

    /** Pretty representation of the attempt score. */
    displayScore: ComputedRef<string | undefined>

    /** Whether the attempt has been scored. */
    isScored: ComputedRef<boolean>
}

export default useAttemptDisplay
