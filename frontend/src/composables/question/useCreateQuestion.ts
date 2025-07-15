/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useRouter } from 'vue-router'

import { generateId } from '@/composables/composableUtils'

/**
 * Composable that generates a new question ID and navigates to the question edit page.
 *
 * @returns A function that, when called, navigates to the edit page of a new question.
 */
function useCreateQuestion() {
    const router = useRouter()

    return () => {
        router.push({ name: 'question-edit', params: { questionId: generateId() } })
    }
}

export default useCreateQuestion
