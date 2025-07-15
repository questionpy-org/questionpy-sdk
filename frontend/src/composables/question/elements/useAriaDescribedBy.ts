/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { computed, type ComputedRef } from 'vue'

/**
 * A composable providing the value for the `aria-describedby` attribute.
 *
 * @param ids The array of ID values.
 *
 * @returns A value for the `aria-describedby` attribute or `undefined`.
 */
function useAriaDescribedBy(ids: (string | undefined)[]): ComputedRef<string | undefined> {
    return computed(() => {
        const filteredIds = ids.filter(Boolean) as string[]
        return filteredIds.length > 0 ? filteredIds.join(' ') : undefined
    })
}

export default useAriaDescribedBy
