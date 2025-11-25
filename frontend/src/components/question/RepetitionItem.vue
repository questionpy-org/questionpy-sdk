<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <div class="hstack gap-3 align-items-start">
        <div class="fs-3 text-body-secondary">{{ number }}.</div>
        <div class="vstack gap-3">
            <FormElement v-for="el in elements" :key="el.name" :disabled="disabled" :element="el" :path-prefix="path" />
        </div>
        <IconButton
            @click="emit('remove')"
            :disabled="removeDisabled"
            :icon-component="IMdiDelete"
            class="align-self-end"
            size="sm"
            variant="danger"
        >
            Remove
        </IconButton>
        <ValidationFeedback :validation="validation" />
    </div>
</template>

<script lang="ts" setup>
import IMdiDelete from '~icons/mdi/delete'

import { useValidation } from '@/composables/question/elements'
import type { ElementPath, RepetitionElement } from '@/types'

const { path } = defineProps<{
    disabled: boolean
    elements: RepetitionElement['elements']
    number: number
    path: ElementPath
    removeDisabled: boolean
}>()
const emit = defineEmits<{ remove: [] }>()

const validation = useValidation(path)
</script>
