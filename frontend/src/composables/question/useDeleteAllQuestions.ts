/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useRouter } from 'vue-router'

import { useConfirmModal } from '@/composables/common'
import { useDeleteAllOptionsFormDataMutation } from '@/queries'
import useAppStateStore from '@/stores/useAppStateStore'

/**
 * Composable that returns a function to delete all question states after displaying a confirmation modal.
 *
 * @returns A function that, when called, shows a confirmation modal and deletes all questions if confirmed.
 */
function useDeleteAllQuestions() {
    const router = useRouter()
    const { mutateAsync } = useDeleteAllOptionsFormDataMutation()
    const { setError } = useAppStateStore()
    const confirmModal = useConfirmModal({
        title: 'Delete All Questions',
        body: 'Are you sure you want to delete all question states?',
        okTitle: 'Delete All Questions',
    })

    return async () => {
        if (await confirmModal()) {
            try {
                await mutateAsync()
            } catch (err) {
                setError(err)
                return
            }

            // Next, navigate to the index page, because the old route may not exist anymore
            if (router.currentRoute.value.name !== 'index') {
                await router.push({ name: 'index' })
            }
        }
    }
}

export default useDeleteAllQuestions
