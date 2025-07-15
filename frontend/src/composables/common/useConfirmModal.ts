/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { useModalController } from 'bootstrap-vue-next'
import { computed, toValue } from 'vue'
import type { ModalOrchestratorShowParam, PublicOrchestratedModal } from 'bootstrap-vue-next'
import type { MaybeRef } from 'vue'

/**
 * Composable that displays a confirmation modal and resolves to `true` only if the user confirms.
 *
 * @param modalProps Optional configuration for the confirmation modal.
 * @returns A function that shows the confirmation modal and resolves to `true` if confirmed, `false` otherwise.
 */
function useConfirmModal(modalProps: MaybeRef<PublicOrchestratedModal | undefined>) {
    const { confirm: confirmModal } = useModalController()

    const modalOptions = computed(
        () =>
            ({
                props: {
                    centered: true,
                    noHeaderClose: true,
                    title: 'Confirmation',
                    body: 'Are you sure?',
                    okTitle: 'Yes',
                    okVariant: 'danger',
                    cancelVariant: 'primary',
                    ...toValue(modalProps),
                },
            }) satisfies ModalOrchestratorShowParam,
    )

    if (!confirmModal) {
        throw new Error('To use modals you need to add the <BModalOrchestrator /> to the component tree.')
    }

    return () => confirmModal(modalOptions.value)
}

export default useConfirmModal
