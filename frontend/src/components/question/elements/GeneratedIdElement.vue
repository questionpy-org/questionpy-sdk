<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <input type="hidden" :id="id" :value="model" />
</template>

<script lang="ts" setup>
import { useId, useModel, usePath } from '@/composables/question/elements'
import type { ElementPath, GeneratedIdElement } from '@/types'

const { element, pathPrefix } = defineProps<{
    element: GeneratedIdElement
    pathPrefix: ElementPath
}>()

const path = usePath(pathPrefix, element)
const id = useId(path)
const model = useModel(pathPrefix, element)
</script>
