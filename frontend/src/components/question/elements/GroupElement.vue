<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BCard class="mb-3" v-show="!isHiddenByCond" :footer="helpText" :id="id" :title="element.label">
        <FormElement
            v-for="el in element.elements"
            :disabled="isDisabled"
            :key="el.name"
            :element="el"
            :path-prefix="[...pathPrefix, element.name]"
        />
    </BCard>
    <BFormText v-if="helpText" :id="helpId">{{ helpText }}</BFormText>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

import { useCommon, useConditions, useHelp, useIsDisabled } from '@/composables/question/elements'
import type { GroupElement } from '@/types'

const { disabled, element, pathPrefix } = defineProps<{
    disabled: boolean
    element: GroupElement
    pathPrefix: string[]
}>()

const { isDisabledByCond, isHiddenByCond } = useConditions(pathPrefix, element)
const { helpId, helpText } = useHelp(pathPrefix, element)
const isDisabled = useIsDisabled(computed(() => disabled || isDisabledByCond.value))

const { id } = useCommon(pathPrefix, element)
</script>
