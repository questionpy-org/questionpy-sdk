<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <div :id="id" class="border-start border-4 mb-3 ps-3">
        <div class="mb-5" v-for="n in count" :key="n">
            <FormElement
                v-for="el in element.elements"
                :disabled="isDisabled"
                :element="el"
                :key="el.name"
                :path-prefix="[...pathPrefix, element.name, n.toString()]"
            />
            <ButtonGroup>
                <IconButton
                    v-if="n === count"
                    @click="add"
                    :disabled="isDisabled"
                    :icon-component="IMdiAdd"
                    size="sm"
                    variant="primary"
                    >{{ element.button_label ?? 'Add repetition' }}</IconButton
                >
                <IconButton
                    @click="remove(n - 1)"
                    :disabled="count <= element.minimum_repetitions || isDisabled"
                    :icon-component="IMdiDelete"
                    size="sm"
                    variant="danger"
                    >Remove</IconButton
                >
            </ButtonGroup>
            <ValidationFeedback :validation="validation" />
        </div>
    </div>
</template>

<script lang="ts" setup>
import IMdiAdd from '~icons/mdi/add'
import IMdiDelete from '~icons/mdi/delete'
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
