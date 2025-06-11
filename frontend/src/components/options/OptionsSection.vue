<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <h3>{{ header }}</h3>
    <FormElement
        v-for="element in elements"
        :disabled="false"
        :element="element"
        :key="element.name"
        :path-prefix="[name]"
    />
</template>

<script lang="ts" setup>
import type { FormElement } from '@/types'

defineProps<{
    elements: FormElement[]
    header: string
    name: string
}>()
</script>
