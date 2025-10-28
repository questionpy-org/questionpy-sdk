/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { isNavigationFailure, useRouter } from 'vue-router'
import type { RouteLocationAsRelative } from 'vue-router'

import { generateId } from '@/composables/composableUtils'
import useAppStateStore from '@/stores/useAppStateStore'
import usePendingOperationsStore from '@/stores/usePendingOperationsStore'
import type { OperationModelType } from '@/stores/usePendingOperationsStore'

/**
 * Composable that provides a function to clone a specific item of a model.
 *
 * The returned function generates a new ID, performs an asynchronous mutation
 * using the provided `makeMutateAsync` function, and manages pending operations
 * during the process. After a successful clone, it navigates to a specified route
 * and triggers a deferred hint for the new item.
 *
 * @param modelType The type of model to clone.
 * @param makeMutateAsync A factory function that receives the new item ID and
 *   returns a function performing the asynchronous clone operation.
 * @param navigateTo The target route to navigate to after cloning is complete.
 * @returns A function that, when invoked, clones the item, manages operations,
 *   navigates to the specified route, triggers a deferred item hint, and returns
 *   the newly generated item ID. Returns `undefined` if an error occurs or
 *   navigation fails.
 */
function useClone(
    modelType: OperationModelType,
    makeMutateAsync: (id: string) => () => Promise<unknown>,
    navigateTo: RouteLocationAsRelative,
) {
    const { setError } = useAppStateStore()
    const { addOperation, removeOperation } = usePendingOperationsStore()
    const router = useRouter()

    return async () => {
        const newId = generateId()

        // 1. Perform the request
        const mutateAsync = makeMutateAsync(newId)
        const cloneOperation = addOperation('clone', { modelType })
        try {
            await mutateAsync()
        } catch (err) {
            setError(err)
            return
        } finally {
            removeOperation(cloneOperation)
        }

        // 2. Navigate to the target route if not already there
        if (router.currentRoute.value.name !== navigateTo.name) {
            const navResult = await router.push(navigateTo)
            if (isNavigationFailure(navResult)) {
                return
            }
        }

        // 3. Schedule a deferred operation for the new item so the UI can highlight it
        addOperation('deferred-item', { modelType, id: newId })

        return newId
    }
}

export default useClone
