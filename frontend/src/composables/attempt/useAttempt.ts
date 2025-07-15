/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, type ComputedRef } from 'vue'
import type { AsyncStatus } from '@pinia/colada'

import {
    useAttemptQuery,
    useDeleteAttemptMutation,
    usePostAttemptMutation,
    usePostAttemptScoreMutation,
} from '@/queries'
import useAppStateStore from '@/stores/useAppStateStore'
import type { AttemptData, SectionErrorMap } from '@/types'

/**
 * Composable that provides stateful attempt data.
 *
 * @param questionId ID of the question.
 * @param attemptId ID of the attempt.
 * @returns An object containing form state and mutation methods.
 */
function useAttempt(questionId: string, attemptId: string): UseAttemptReturn {
    const { asyncStatus: dataAsyncStatus, data: attemptData, error: dataError } = useAttemptQuery(questionId, attemptId)
    const { asyncStatus: postAsyncStatus, mutateAsync: postAttempt } = usePostAttemptMutation(questionId, attemptId)
    const { asyncStatus: deleteAttemptAsyncStatus, mutateAsync: deleteAttempt } = useDeleteAttemptMutation(
        questionId,
        attemptId,
    )
    const { asyncStatus: postScoreAsyncStatus, mutateAsync: postScore } = usePostAttemptScoreMutation(
        questionId,
        attemptId,
    )

    const { setError } = useAppStateStore()

    return {
        asyncStatus: computed(() =>
            [dataAsyncStatus, postAsyncStatus, deleteAttemptAsyncStatus, postScoreAsyncStatus].every(
                ({ value }) => value === 'idle',
            )
                ? 'idle'
                : 'loading',
        ),
        error: computed(() => dataError.value),

        attemptData: computed(() => attemptData.value?.attempt_data),
        iframeSrcDoc: computed(() => attemptData.value?.attempt_html),
        renderErrors: computed(() => attemptData.value?.render_errors),

        isRescoreDisabled: computed(() => attemptData.value?.attempt_data.attempt_status !== 'SCORED'),
        isRestartDisabled: computed(() => attemptData.value?.attempt_data.attempt_status === 'STARTED'),

        async save(formData) {
            try {
                await postAttempt(formData)
            } catch (err) {
                setError(err)
            }
        },

        async score() {
            try {
                await postScore()
            } catch (err) {
                setError(err)
            }
        },

        async restart() {
            try {
                await deleteAttempt()
            } catch (err) {
                setError(err)
            }
        },
    }
}

/** Encapsulates reactive state and mutation methods for an attempt. */
interface UseAttemptReturn {
    /** Attempt data. */
    attemptData: ComputedRef<AttemptData | undefined>

    /** Computed combined async loading status. */
    asyncStatus: ComputedRef<AsyncStatus>

    /** Computed reference to the latest error from underlying queries. */
    error: ComputedRef<Error | null>

    /** The iframe's HTML source. */
    iframeSrcDoc: ComputedRef<string | undefined>

    /** The attempt's render errors. */
    renderErrors: ComputedRef<SectionErrorMap | undefined>

    /** Whether the rescore action is currently disabled. */
    isRescoreDisabled: ComputedRef<boolean>

    /** Whether the restart action is currently disabled. */
    isRestartDisabled: ComputedRef<boolean>

    /**
     * Saves the attempt.
     *
     * @param formData The attempt data to save.
     */
    save(formData: Record<string, unknown>): Promise<void>

    /** Score the attempt. */
    score(): Promise<void>

    /** Restart the attempt. */
    restart(): Promise<void>
}

export default useAttempt
export type { UseAttemptReturn }
