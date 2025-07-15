<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <FormGroup v-show="!isHiddenByCond" :label="element.label">
        <BFormSelect
            v-model="model"
            :aria-describedby="ariaDescribedBy"
            :disabled="isDisabled"
            :id="id"
            :multiple="element.multiple"
            :name="name"
            :options="options"
            :required="element.required"
            :select-size="size"
        />
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
} from '@/composables/question/elements'
import type { SelectElement } from '@/types'

const { disabled, element, pathPrefix } = defineProps<{
    disabled: boolean
    element: SelectElement
    pathPrefix: string[]
}>()

const MAX_SIZE = 8
const size = computed(() => (element.multiple ? Math.min(element.options.length, MAX_SIZE) : undefined))

const { id, name } = useCommon(pathPrefix, element)
const model = useModel(pathPrefix, element)
const { isDisabledByCond, isHiddenByCond } = useConditions(pathPrefix, element)
const { helpId, helpText } = useHelp(pathPrefix, element)
const isDisabled = useIsDisabled(computed(() => disabled || isDisabledByCond.value))
const ariaDescribedBy = useAriaDescribedBy([helpId.value])

const options = computed(() =>
    element.options.map((opts) => ({
        text: opts.label,
        value: opts.value,
    })),
)
</script>
