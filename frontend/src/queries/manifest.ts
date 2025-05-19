/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineQuery, useQuery } from '@pinia/colada'
import { computed } from 'vue'

import { manifestSchema } from '@/schema/manifest'

import { get } from './fetch'

/** Package manifest query. */
const useManifest = defineQuery(() => {
    const query = useQuery({
        key: ['manifest'],
        query: () => get('manifest', manifestSchema),
    })

    const manifest = computed(() => {
        const { data } = query.state.value
        return data
            ? {
                  ...data,
                  packageIdentifier: `${data.namespace}/${data.short_name}`,
                  name: data.name.en,
                  iconSrc: data.icon ?? undefined,
                  description: data.description.en,
                  languages: data.languages.join(', '),
                  url: data.url,
              }
            : undefined
    })

    return { manifest, ...query }
})

export default useManifest
