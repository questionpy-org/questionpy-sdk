<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <FormGroup v-show="!isHiddenByCond" :label="element.label">
        <BFormInput
            type="text"
            v-model="model"
            :aria-describedby="ariaDescribedBy"
            :disabled="isDisabled"
            :id="id"
            :name="name"
            :placeholder="element.placeholder ?? undefined"
            :required="element.required"
            :state="validationState"
        />
        <BFormInvalidFeedback v-if="validationText" :id="validationId" :state="validationState">{{
            validationText
        }}</BFormInvalidFeedback>
        <BFormText v-if="helpText" :id="helpId">{{ helpText }}</BFormText>
    </FormGroup>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import {
    useAriaDescribedBy,
    useCommon,
    useConditions,
    useHelp,
    useIsDisabled,
    useModel,
    useValidation,
} from '@/composables/question/elements'
import type { TextInputElement } from '@/types'

const { disabled, element, pathPrefix } = defineProps<{
    disabled: boolean
    element: TextInputElement
    pathPrefix: string[]
}>()

const { id, name } = useCommon(pathPrefix, element)
const model = useModel(pathPrefix, element)
const { isDisabledByCond, isHiddenByCond } = useConditions(pathPrefix, element)
const { validationId, validationText, validationState } = useValidation(pathPrefix, element)
const { helpId, helpText } = useHelp(pathPrefix, element)
const isDisabled = useIsDisabled(computed(() => disabled || isDisabledByCond.value))
const ariaDescribedBy = useAriaDescribedBy([helpId.value])
</script>
