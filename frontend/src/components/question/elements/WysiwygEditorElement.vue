<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <FormGroup :label="element.label" :state="validation.state">
        <TinyMCE v-model="model" :disabled="isDisabled" :id="id" />
        <ValidationFeedback :validation="validation" />
        <BFormText v-if="helpText" :id="helpId">{{ helpText }}</BFormText>
    </FormGroup>
</template>

<script lang="ts" setup>
import { useHelp, useId, useIsDisabled, useModel, usePath, useValidation } from '@/composables/question/elements'
import type { ElementPath, WysiwygEditorElement } from '@/types'

const { element, pathPrefix } = defineProps<{
    element: WysiwygEditorElement
    pathPrefix: ElementPath
}>()

const path = usePath(pathPrefix, element)
const id = useId(path)
const model = useModel(pathPrefix, element)
const { helpId, helpText } = useHelp(pathPrefix, element)
const validation = useValidation(path)
const isDisabled = useIsDisabled()
</script>
