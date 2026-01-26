<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BCard v-show="!isHiddenByCond" :footer="helpText" :id="id" :title="element.label">
        <BContainer fluid gutter-x="0">
            <BRow ref="row">
                <BCol v-for="el in element.elements" :key="el.name" :class="columnClass">
                    <FormElement :disabled="isDisabled" :element="el" :path-prefix="[...pathPrefix, element.name]" />
                </BCol>
            </BRow>
        </BContainer>
    </BCard>
</template>

<script lang="ts" setup>
import { breakpointsBootstrapV5, useBreakpoints, useResizeObserver } from '@vueuse/core'
import { computed, ref, useTemplateRef } from 'vue'

import { useConditions, useHelp, useId, useIsDisabled, usePath } from '@/composables/question/elements'
import type { ElementPath, GroupElement } from '@/types'

const { disabled, element, pathPrefix } = defineProps<{
    disabled: boolean
    element: GroupElement
    pathPrefix: ElementPath
}>()

const path = usePath(pathPrefix, element)
const id = useId(path)
const { isDisabledByCond, isHiddenByCond } = useConditions(pathPrefix, element)
const { helpText } = useHelp(pathPrefix, element)
const isDisabled = useIsDisabled(computed(() => disabled || isDisabledByCond.value))

const breakpoints = useBreakpoints(breakpointsBootstrapV5)
const el = useTemplateRef('row')

function getColumnClass() {
    // Fit elements horizontally, but...
    const base = Math.floor(12 / element.elements.length)

    // ...max 3 (xxl)
    if (breakpoints.isGreaterOrEqual('xxl')) {
        return `col-xxl-${Math.max(4, base)}`
    }

    // ...max 2 (xl)
    if (breakpoints.isGreaterOrEqual('xl')) {
        return `col-xl-${Math.max(6, base)}`
    }

    // ..max 1 (<xl)
    return 'col-12'
}

const columnClass = ref(getColumnClass())

useResizeObserver(el, () => {
    columnClass.value = getColumnClass()
})
</script>
