<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <component :is="elementComponent" v-bind="elementProps" />
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import type { ComponentInstance } from 'vue'

import type { FormElement } from '@/types'

import { mapElementKindToComponent } from './elements'

const props = defineProps<{
    disabled: boolean
    element: FormElement
    pathPrefix: string[]
}>()

const elementComponent = computed(() => mapElementKindToComponent(props.element.kind))
const elementProps = props as ComponentInstance<typeof elementComponent.value>['$props']
</script>
