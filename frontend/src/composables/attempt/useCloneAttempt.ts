/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useClone } from '@/composables/common'
import { usePostAttemptCloneMutation } from '@/queries'

/**
 * Composable that returns a function to clone an attempt.
 *
 * @param questionId The ID of the question the attempt belongs to.
 * @param attemptId The ID of the attempt to clone.
 * @returns The ID of the new attempt.
 */
function useCloneAttempt(questionId: string, attemptId: string) {
    const makeMutateAsync = (newId: string) => usePostAttemptCloneMutation(questionId, attemptId, newId).mutateAsync
    const navigateTo = { name: 'question', params: { questionId } } as const
    return useClone('attempt', makeMutateAsync, navigateTo)
}

export default useCloneAttempt
