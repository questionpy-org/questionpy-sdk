<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <h3>{{ header }}</h3>
    <template v-for="element in elements" :key="element.name">
        <ErrorBoundary>
            <FormElement :disabled="false" :element="element" :path-prefix="[name]" />
        </ErrorBoundary>
    </template>
</template>

<script lang="ts" setup>
import type { FormElement } from '@/types'

defineProps<{
    elements: FormElement[]
    header: string
    name: string
}>()
</script>
