/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useRouter } from 'vue-router'

import { generateId } from '@/composables/composableUtils'

/**
 * Composable that generates a new attempt ID and navigates to the attempt page.
 *
 * @param questionId The ID of the question the new attempt belongs to.
 * @returns A function that, when called, navigates to the edit page of a new attempt.
 */
function useCreateAttempt(questionId: string) {
    const router = useRouter()

    return () => {
        router.push({ name: 'question-attempt', params: { questionId, attemptId: generateId() } })
    }
}

export default useCreateAttempt
