/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useClone } from '@/composables/common'
import { usePostQuestionCloneMutation } from '@/queries'

/**
 * Composable that returns a function to clone a question.
 *
 * @param questionId The ID of the question to clone.
 * @returns The ID of the new question.
 */
function useCloneQuestion(questionId: string) {
    const makeMutateAsync = (newId: string) => usePostQuestionCloneMutation(questionId, newId).mutateAsync
    const navigateTo = { name: 'index' } as const
    return useClone('question', makeMutateAsync, navigateTo)
}

export default useCloneQuestion
