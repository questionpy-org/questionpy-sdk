/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { generateId } from '@/composables/composableUtils'
import { usePostQuestionCloneMutation } from '@/queries'
import useAppStateStore from '@/stores/useAppStateStore'

/**
 * Composable that returns a function to clone a question.
 *
 * @param questionId The ID of the question to clone.
 * @returns The ID of the new question.
 */
function useCloneQuestion(questionId: string) {
    const newQuestionId = generateId()
    const { mutateAsync } = usePostQuestionCloneMutation(questionId, newQuestionId)
    const { setError } = useAppStateStore()

    return async () => {
        try {
            await mutateAsync()
            return newQuestionId
        } catch (err) {
            setError(err)
        }
    }
}
export default useCloneQuestion
