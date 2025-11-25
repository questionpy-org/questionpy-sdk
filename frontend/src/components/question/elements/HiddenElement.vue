<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <input :disabled="isDisabled" type="hidden" :id="id" :value="element.value" />
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import { useConditions, useId, useIsDisabled, usePath } from '@/composables/question/elements'
import type { ElementPath, HiddenElement } from '@/types'

const { disabled, element, pathPrefix } = defineProps<{
    disabled: boolean
    element: HiddenElement
    pathPrefix: ElementPath
}>()

const path = usePath(pathPrefix, element)
const id = useId(path)
const { isDisabledByCond } = useConditions(pathPrefix, element)
const isDisabled = useIsDisabled(computed(() => disabled || isDisabledByCond.value))
</script>
