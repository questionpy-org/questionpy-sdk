<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <input type="hidden" :name="name" :value="model" />
</template>

<script lang="ts" setup>
import type { GeneratedIdElement } from '@/schema/options/types'

import { useCommon, useModel } from './composables'

const { element, pathPrefix } = defineProps<{
    element: GeneratedIdElement
    pathPrefix: string[]
}>()
const { name } = useCommon(pathPrefix, element)
const model = useModel(pathPrefix, element)
</script>
