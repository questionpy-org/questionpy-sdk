<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <input type="hidden" :id="id" :name="name" :value="model" />
</template>

<script lang="ts" setup>
import { useCommon, useModel } from '@/composables/question/elements'
import type { GeneratedIdElement } from '@/types'

const { element, pathPrefix } = defineProps<{
    element: GeneratedIdElement
    pathPrefix: string[]
}>()
const { id, name } = useCommon(pathPrefix, element)
const model = useModel(pathPrefix, element)
</script>
