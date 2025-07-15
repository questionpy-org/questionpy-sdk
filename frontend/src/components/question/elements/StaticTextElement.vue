<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <FormGroup v-show="!isHiddenByCond" :label="element.label">
        <p>{{ element.text }}</p>
        <BFormText v-if="helpText" :id="helpId">{{ helpText }}</BFormText>
    </FormGroup>
</template>

<script lang="ts" setup>
import { useConditions, useHelp } from '@/composables/question/elements'
import type { StaticTextElement } from '@/types'

const { element, pathPrefix } = defineProps<{
    element: StaticTextElement
    pathPrefix: string[]
}>()

const { isHiddenByCond } = useConditions(pathPrefix, element)
const { helpId, helpText } = useHelp(pathPrefix, element)
</script>
