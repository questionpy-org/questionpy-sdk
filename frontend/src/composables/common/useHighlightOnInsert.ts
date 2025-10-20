/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { nextTick, onMounted, type Ref, ref, watch } from 'vue'

/**
 * Composable for scrolling to and temporarily highlighting items when they are added or referenced in history.
 *
 * The composable tracks items by ID, scrolls them into view, and exposes which IDs are currently highlighted.
 *
 * @template T - Type of the items in the collection.
 * @param items Reactive object mapping IDs to items.
 * @param idGenerator Function to generate the HTML element ID from an item ID.
 * @param options Optional configuration:
 *   - `historyStateKey`: Key in `history.state` to check for an initial item to highlight (default: `'highlightId'`).
 *   - `scrollBehavior`: Scroll options for `scrollIntoView` (default: `{ behavior: 'smooth', block: 'center' }`).
 *   - `highlightDelay`: Time to wait before highlighting to compensate for scrolling delay.
 * @returns Object with:
 *   - `handleNewItem(id: string)`: Add an ID to be scrolled to and highlighted when it appears.
 *   - `highlightedIds`: Reactive set of IDs currently highlighted.
 */
function useHighlightOnInsert<T>(
    items: Ref<Record<string, T>>,
    idGenerator: (id: string) => string,
    options: {
        historyStateKey?: string
        scrollBehavior?: ScrollIntoViewOptions
        highlightDelay?: 600
    } = {},
) {
    // Default options
    const {
        historyStateKey = 'highlightId',
        scrollBehavior = {
            behavior: 'smooth',
            block: 'center',
        },
    } = options

    const pendingIds = ref<Set<string>>(new Set())
    const highlightedIds = ref<Set<string>>(new Set())

    // Handle highlighting after navigation
    onMounted(() => {
        const highlightId = history.state?.[historyStateKey]
        if (typeof highlightId === 'string') {
            pendingIds.value.add(highlightId)
        }
    })

    // Watch for pending items to appear in the list
    watch(items, async (newItems, oldItems) => {
        for (const id of pendingIds.value) {
            if (newItems[id] && !oldItems?.[id]) {
                pendingIds.value.delete(id)
                await nextTick()

                const el = document.getElementById(idGenerator(id))
                if (el) {
                    el.scrollIntoView(scrollBehavior)
                    // Unfortunately, scrollIntoView does not return a Promise
                    setTimeout(() => {
                        highlightedIds.value.add(id)
                        el.addEventListener(
                            'animationend',
                            () => {
                                highlightedIds.value.delete(id)
                            },
                            { once: true },
                        )
                    }, options.highlightDelay)
                }
            }
        }
    })

    return {
        handleNewItem: (id: string) => {
            pendingIds.value.add(id)
        },
        highlightedIds,
    }
}

export default useHighlightOnInsert
