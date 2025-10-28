/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useRouter } from 'vue-router'

import { useConfirmModal } from '@/composables/common'
import { useDeleteAttemptMutation } from '@/queries'
import useAppStateStore from '@/stores/useAppStateStore'
import usePendingOperationsStore from '@/stores/usePendingOperationsStore'

/**
 * Composable that returns a function to delete an attempt after displaying a confirmation modal.
 *
 * @param questionId The ID of the question the attempt belongs to.
 * @param attemptId The ID of the attempt to delete.
 * @returns A function that, when called, shows a confirmation modal and deletes the question if confirmed.
 */
function useDeleteAttempt(questionId: string, attemptId: string) {
    const { mutateAsync } = useDeleteAttemptMutation(questionId, attemptId)
    const { setError } = useAppStateStore()
    const { addOperation, removeOperation } = usePendingOperationsStore()
    const router = useRouter()

    const confirmModal = useConfirmModal({
        title: 'Delete Attempt',
        body: 'Are you sure you want to delete this attempt?',
        okTitle: 'Delete Attempt',
    })

    return async () => {
        if (await confirmModal()) {
            // Navigate away from attempt preview page *before* deleting to prevent re-creation
            if (router.currentRoute.value.name === 'question-attempt') {
                await router.push({ name: 'question', params: { questionId } })
            }

            const operation = addOperation('delete', { modelType: 'attempt' })
            try {
                await mutateAsync()
            } catch (err) {
                setError(err)
                return
            } finally {
                removeOperation(operation)
            }
        }
    }
}

export default useDeleteAttempt
