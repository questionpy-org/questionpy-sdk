<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <FormGroup v-show="!isHiddenByCond" :label="element.label" :state="validation.state">
        <BFormRadioGroup
            v-model="model"
            :aria-describedby="ariaDescribedBy"
            :disabled="isDisabled"
            :id="id"
            :options="options"
            :required="element.required"
            :state="validation.state"
        />
        <ValidationFeedback :validation="validation" />
        <BFormText v-if="helpText" :id="helpId">{{ helpText }}</BFormText>
    </FormGroup>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

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
import type { ElementPath, RadioGroupElement } from '@/types'

const { disabled, element, pathPrefix } = defineProps<{
    disabled: boolean
    element: RadioGroupElement
    pathPrefix: ElementPath
}>()

const path = usePath(pathPrefix, element)
const id = useId(path)
const model = useModel(pathPrefix, element)
const { isDisabledByCond, isHiddenByCond } = useConditions(pathPrefix, element)
const { helpId, helpText } = useHelp(pathPrefix, element)
const isDisabled = useIsDisabled(computed(() => disabled || isDisabledByCond.value))
const ariaDescribedBy = useAriaDescribedBy([helpId.value])
const options = computed(() => element.options.map(({ value, label }) => ({ value, text: label })))
const validation = useValidation(path)
</script>
