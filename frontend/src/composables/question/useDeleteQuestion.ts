/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useConfirmModal } from '@/composables/common'
import { useDeleteOptionsFormDataMutation } from '@/queries'
import useAppStateStore from '@/stores/useAppStateStore'

/**
 * Composable that returns a function to delete a question after displaying a confirmation modal.
 *
 * @param questionId The ID of the question to delete.
 * @returns A function that, when called, shows a confirmation modal and deletes the question if confirmed.
 */
function useDeleteQuestion(questionId: string) {
    const { mutateAsync } = useDeleteOptionsFormDataMutation(questionId)
    const { setError } = useAppStateStore()
    const confirmModal = useConfirmModal({
        title: 'Delete Question',
        body: 'Are you sure you want to delete this question?',
        okTitle: 'Delete Question',
    })

    return async () => {
        if (await confirmModal()) {
            try {
                await mutateAsync()
            } catch (err) {
                setError(err)
            }
        }
    }
}

export default useDeleteQuestion
