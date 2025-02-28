<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <FormGroup v-show="!isHiddenByCond" :label="element.left_label">
        <BFormCheckbox
            :aria-describedby="ariaDescribedBy"
            :disabled="isDisabled"
            :name="name"
            :required="element.required"
            v-model="model"
            >{{ element.right_label }}</BFormCheckbox
        >
        <BFormText v-if="helpText" :id="helpId">{{ helpText }}</BFormText>
    </FormGroup>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import type { CheckboxElement } from '@/schema/options/types'

import { useAriaDescribedBy, useCommon, useConditions, useHelp, useIsDisabled, useModel } from './composables'

const { disabled, element, pathPrefix } = defineProps<{
    disabled: boolean
    element: CheckboxElement
    pathPrefix: string[]
}>()

const { name } = useCommon(pathPrefix, element)
const model = useModel(pathPrefix, element)
const { isDisabledByCond, isHiddenByCond } = useConditions(pathPrefix, element)
const { helpId, helpText } = useHelp(pathPrefix, element)
const isDisabled = useIsDisabled(computed(() => disabled || isDisabledByCond.value))
const ariaDescribedBy = useAriaDescribedBy([helpId.value])
</script>
