/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, type ComputedRef } from 'vue'

import {
    useAttemptQuery,
    useDeleteAttemptMutation,
    usePostAttemptMutation,
    usePostAttemptScoreMutation,
} from '@/queries'
import useAppStateStore from '@/stores/useAppStateStore'
import usePendingOperationsStore from '@/stores/usePendingOperationsStore'
import type { AttemptData, SectionErrorMap } from '@/types'

/**
 * Composable that provides stateful attempt data.
 *
 * @param questionId ID of the question.
 * @param attemptId ID of the attempt.
 * @returns An object containing form state and mutation methods.
 */
function useAttempt(questionId: string, attemptId: string): UseAttemptReturn {
    const { data: attemptData, error: dataError, isPending } = useAttemptQuery(questionId, attemptId)
    const { mutateAsync: postAttempt } = usePostAttemptMutation(questionId, attemptId)
    const { mutateAsync: deleteAttempt } = useDeleteAttemptMutation(questionId, attemptId)
    const { mutateAsync: postScore } = usePostAttemptScoreMutation(questionId, attemptId)

    const { setError } = useAppStateStore()
    const { addOperation, removeOperation } = usePendingOperationsStore()

    return {
        isPending,
        error: computed(() => dataError.value),

        attemptData: computed(() => attemptData.value?.attempt_data),
        iframeSrcDoc: computed(() => attemptData.value?.attempt_html),
        renderErrors: computed(() => attemptData.value?.render_errors),

        isRescoreDisabled: computed(() => attemptData.value?.attempt_data.attempt_status !== 'SCORED'),
        isRestartDisabled: computed(() => attemptData.value?.attempt_data.attempt_status === 'STARTED'),

        async save(formData) {
            const operation = addOperation('submit', { modelType: 'attempt' })
            try {
                await postAttempt(formData)
            } catch (err) {
                setError(err)
            } finally {
                removeOperation(operation)
            }
        },

        async score() {
            const operation = addOperation('score')
            try {
                await postScore()
            } catch (err) {
                setError(err)
            } finally {
                removeOperation(operation)
            }
        },

        async restart() {
            const operation = addOperation('delete', { modelType: 'attempt' })
            try {
                await deleteAttempt()
            } catch (err) {
                setError(err)
            } finally {
                removeOperation(operation)
            }
        },
    }
}

/** Encapsulates reactive state and mutation methods for an attempt. */
interface UseAttemptReturn {
    /** Attempt data. */
    attemptData: ComputedRef<AttemptData | undefined>

    /** Whether the request is still pending its first call. */
    isPending: ComputedRef<boolean>

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
