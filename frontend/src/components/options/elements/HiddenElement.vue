<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <input :disabled="isDisabled" type="hidden" :name="name" :value="element.value" />
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import type { HiddenElement } from '@/schema/options/types'

import { useCommon, useConditions, useIsDisabled } from './composables'

const { disabled, element, pathPrefix } = defineProps<{
    disabled: boolean
    element: HiddenElement
    pathPrefix: string[]
}>()

const { name } = useCommon(pathPrefix, element)
const { isDisabledByCond } = useConditions(pathPrefix, element)
const isDisabled = useIsDisabled(computed(() => disabled || isDisabledByCond.value))
</script>
