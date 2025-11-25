<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BCard :id="id" no-body>
        <BListGroup flush>
            <BListGroupItem v-for="n in count" :key="n" class="p-3">
                <RepetitionItem
                    @remove="remove(n - 1)"
                    :number="n"
                    :disabled="disabled"
                    :remove-disabled="count <= element.minimum_repetitions || isDisabled"
                    :elements="element.elements"
                    :path="[...pathPrefix, element.name, n - 1]"
                />
            </BListGroupItem>
        </BListGroup>
        <template #footer>
            <ButtonGroup>
                <IconButton @click="add" :disabled="isDisabled" :icon-component="IMdiAdd" size="sm" variant="primary">{{
                    element.button_label ?? 'Add repetition'
                }}</IconButton>
            </ButtonGroup>
            <ValidationFeedback :validation="validation" />
        </template>
    </BCard>
</template>

<script lang="ts" setup>
import IMdiAdd from '~icons/mdi/add'
import { computed } from 'vue'

import { useRepetitions } from '@/composables/question'
import { useId, useIsDisabled, usePath, useValidation } from '@/composables/question/elements'
import type { ElementPath, RepetitionElement } from '@/types'

const { disabled, element, pathPrefix } = defineProps<{
    disabled: boolean
    element: RepetitionElement
    pathPrefix: ElementPath
}>()

const path = usePath(pathPrefix, element)
const id = useId(path)
const { add, count, remove } = useRepetitions(pathPrefix, element)
const isDisabled = useIsDisabled(computed(() => disabled))
const validation = useValidation(path)
</script>
