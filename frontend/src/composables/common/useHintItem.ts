/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { type ComponentPublicInstance, ref } from 'vue'

/**
 * Composable for scrolling to an item and temporarily highlighting it in the DOM.
 *
 * The composable tracks items by ID, scrolls them into view, and exposes which IDs are currently highlighted.
 *
 * @param options Optional configuration:
 *   - `highlightDelay`: Time to wait before highlighting to compensate for scrolling delay.
 *   - `scrollBehavior`: Scroll options for `scrollIntoView` (default: `{ behavior: 'smooth', block: 'center' }`).
 * @returns Object with:
 *   - `highlightedIds`: Reactive set of IDs currently highlighted.
 *   - `hintItem(id)`: Scrolls the item into view and adds it to `highlightedIds` temporarily.
 *   - `registerElementRef(id)`: Returns a ref registration function for the given ID; should be bound to
 *     the element in the template.
 */
function useHintItem(
    options: {
        highlightDelay?: number
        scrollBehavior?: ScrollIntoViewOptions
    } = {},
) {
    // Default options
    const {
        highlightDelay = 600,
        scrollBehavior = {
            behavior: 'smooth',
            block: 'center',
        },
    } = options

    const highlightedIds = ref<Set<string>>(new Set())
    const elements = ref<Record<string, HTMLElement>>({})

    const registerElementRef = (attemptId: string) => (el: Element | ComponentPublicInstance | null) => {
        if (el) {
            if (el instanceof HTMLElement) {
                elements.value[attemptId] = el
            }
        } else {
            // Cleanup on unmount
            delete elements.value[attemptId]
        }
    }

    const hintItem = (id: string) =>
        new Promise<void>((resolve) => {
            const el = elements.value[id]
            let fallbackTimeout: number | null = null

            if (!el) {
                return resolve()
            }

            el.scrollIntoView(scrollBehavior)

            const removeId = () => {
                highlightedIds.value.delete(id)
                resolve()
            }

            // Just in case 'animationend' never fires
            fallbackTimeout = window.setTimeout(removeId, 3000)

            // Unfortunately, scrollIntoView does not return a Promise :(
            window.setTimeout(() => {
                highlightedIds.value.add(id)
                el.addEventListener(
                    'animationend',
                    () => {
                        if (fallbackTimeout) {
                            window.clearTimeout(fallbackTimeout)
                        }
                        removeId()
                    },
                    { once: true },
                )
            }, highlightDelay)
        })

    return { highlightedIds, hintItem, registerElementRef }
}

export default useHintItem
