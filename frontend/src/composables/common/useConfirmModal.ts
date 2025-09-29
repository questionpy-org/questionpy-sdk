/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useModal } from 'bootstrap-vue-next'
import { computed, toValue } from 'vue'
import type { ModalOrchestratorCreateParam } from 'bootstrap-vue-next'
import type { MaybeRef } from 'vue'

/**
 * Composable that displays a confirmation modal and resolves to `true` only if the user confirms.
 *
 * @param modalProps Optional configuration for the confirmation modal.
 * @returns A function that shows the confirmation modal and resolves to `true` if confirmed, `false` otherwise.
 */
function useConfirmModal(modalProps: MaybeRef<ModalOrchestratorCreateParam | undefined>) {
    const { create } = useModal()

    const modalOptions = computed(
        () =>
            ({
                centered: true,
                noHeaderClose: true,
                title: 'Confirmation',
                body: 'Are you sure?',
                okTitle: 'Yes',
                okVariant: 'danger',
                cancelVariant: 'primary',
                ...toValue(modalProps),
            }) satisfies ModalOrchestratorCreateParam,
    )

    return async () => {
        const modal = create(modalOptions)
        const result = await modal.show()
        modal.destroy()
        return Boolean(result === null || typeof result === 'boolean' ? result : result.ok)
    }
}

export default useConfirmModal
