/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, nextTick, toValue, watch } from 'vue'
import type { MaybeRefOrGetter } from 'vue'

import usePendingOperationsStore from '@/stores/usePendingOperationsStore'
import type { OperationModelType } from '@/stores/usePendingOperationsStore'

/**
 * Composable for handling deferred operations on a reactive collection of items.
 *
 * This composable watches both a reactive item map (`items`) and the pending operations store. When a
 * `deferred-item` operation matches the given `modelType` and the corresponding item becomes available in `items`,
 * it calls the provided `handleDeferredItem` callback with the item's ID and removes the operation from the store.
 *
 * Use this when you want to react to items that are expected to appear asynchronously, ensuring that the callback
 * is invoked only once the item exists.
 *
 * @template T Type of items stored in the `items` map.
 * @param modelType The model type to filter relevant deferred operations.
 * @param items An object mapping item IDs to items (ref or getter).
 * @param handleDeferredItem Callback invoked with the item ID once it appears.
 */
function useDeferredItem<T extends object>(
    modelType: OperationModelType,
    items: MaybeRefOrGetter<Record<string, T>>,
    handleDeferredItem: (id: string) => Promise<void>,
) {
    const { getOperationsByType, removeOperation } = usePendingOperationsStore()
    const deferredItemOperations = computed(() => getOperationsByType('deferred-item'))

    watch(
        () => ({
            newOps: deferredItemOperations.value,
            newItems: toValue(items),
        }),
        async ({ newOps, newItems }) => {
            // Check for an operation that concerns us
            for (const op of newOps) {
                if (op.modelType === modelType) {
                    // Check if the item is available
                    if (newItems[op.id]) {
                        // Ensure Vue updated the DOM
                        await nextTick()

                        try {
                            await handleDeferredItem(op.id)
                        } finally {
                            removeOperation(op)
                        }
                    }
                }
            }
        },
        { immediate: true },
    )
}

export default useDeferredItem
