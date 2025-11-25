<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <FormGroup v-show="!isHiddenByCond" :label="element.left_label" :state="validation.state">
        <BFormCheckbox
            :aria-describedby="ariaDescribedBy"
            :disabled="isDisabled"
            :id="id"
            :required="element.required"
            :state="validation.state"
            v-model="model"
            >{{ element.right_label }}</BFormCheckbox
        >
        <ValidationFeedback :validation="validation" />
        <BFormText v-if="helpText" :id="helpId">{{ helpText }}</BFormText>
    </FormGroup>
</template>

<script lang="ts" setup>
import ValidationFeedback from '@/components/question/ValidationFeedback.vue'
import {
    useAriaDescribedBy,
    useConditions,
    useHelp,
    useId,
    useIsDisabled,
    useModel,
    usePath,
    useValidation,
} from '@/composables/question/elements'
import type { CheckboxElement, ElementPath } from '@/types'

const { disabled, element, pathPrefix } = defineProps<{
    disabled: boolean
    element: CheckboxElement
    pathPrefix: ElementPath
}>()

const path = usePath(pathPrefix, element)
const id = useId(path)
const model = useModel(pathPrefix, element)
const { isDisabledByCond, isHiddenByCond } = useConditions(pathPrefix, element)
const { helpId, helpText } = useHelp(pathPrefix, element)
const isDisabled = useIsDisabled(() => disabled || isDisabledByCond.value)
const ariaDescribedBy = useAriaDescribedBy([helpId.value])
const validation = useValidation(path)
</script>
