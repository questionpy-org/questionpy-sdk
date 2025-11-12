<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <div :id="id" ref="targetElement"></div>
</template>

<script lang="ts" setup>
// Loosely based on
// - https://www.tiny.cloud/docs/tinymce/latest/vite-es6-npm/
// - https://github.com/tinymce/tinymce-vue

import { ref, watch } from 'vue'
import type { RawEditorOptions } from 'tinymce/tinymce'

import type { RichTextEditor } from '@/types'

import useTinyMCEInstance from './useTinyMCEInstance'

const {
    disabled = false,
    id,
    initOptions: tineMCEOptions = {},
    modelValue,
} = defineProps<{
    disabled?: boolean
    id: string
    initOptions?: RawEditorOptions
    modelValue?: RichTextEditor
}>()

const emit = defineEmits<{
    (e: 'update:modelValue', value: RichTextEditor): void
}>()

const targetElement = ref<HTMLDivElement | undefined>()

// Pass editor updates to model
function onUpdate(state: RichTextEditor) {
    emit('update:modelValue', state)
}

const editorInstance = useTinyMCEInstance({
    targetElement,
    onUpdate,
    initialState: modelValue ?? { text: '', files: [] },
    tinyMCEOptions: { ...tineMCEOptions, disabled },
})

// Pass model value updates to editor
watch(
    () => modelValue,
    (newValue) => {
        if (editorInstance && newValue?.text !== editorInstance.getContent()) {
            editorInstance.setContent(newValue?.text ?? '')
        }
    },
)

watch(
    () => disabled,
    (newValue) => {
        if (editorInstance) {
            editorInstance.options.set('disabled', newValue)
        }
    },
)
</script>

<style lang="scss" src="./TinyMCEUI.scss" />
