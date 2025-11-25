<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BCard v-show="!isHiddenByCond" :footer="helpText" :id="id" :title="element.label">
        <div class="vstack gap-3">
            <FormElement
                v-for="el in element.elements"
                :disabled="isDisabled"
                :key="el.name"
                :element="el"
                :path-prefix="[...pathPrefix, element.name]"
            />
        </div>
    </BCard>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

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
</script>
