/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { generateId } from '@/composables/composableUtils'
import { usePostAttemptCloneMutation } from '@/queries'
import useAppStateStore from '@/stores/useAppStateStore'

/**
 * Composable that returns a function to clone an attempt.
 *
 * @param questionId The ID of the question the attempt belongs to.
 * @param attemptId The ID of the attempt to clone.
 * @returns The ID of the new attempt.
 */
function useCloneAttempt(questionId: string, attemptId: string) {
    const newAttemptId = generateId()
    const { mutateAsync } = usePostAttemptCloneMutation(questionId, attemptId, newAttemptId)
    const { setError } = useAppStateStore()

    return async () => {
        try {
            await mutateAsync()
            return newAttemptId
        } catch (err) {
            setError(err)
        }
    }
}

export default useCloneAttempt
