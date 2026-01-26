<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <FormGroup :label="element.label" :state="validation.state">
        <BFormFile
            v-model="toUpload"
            :aria-describedby="ariaDescribedBy"
            :disabled="isDisabled"
            :id="id"
            :state="validation.state"
            multiple
        />
        <!-- File selector -->
        <BOverlay :show="isUploading" opacity="0.3" rounded="sm">
            <template #overlay>
                <BSpinner class="mx-1" label="Uploading…" small />
                Uploading…
            </template>
        </BOverlay>

        <!-- Thumbnails / file list -->
        <BContainer class="mt-3">
            <BRow class="gap-1 gap-md-2">
                <BCol v-for="(file, idx) in model" :key="file.file_ref" class="flex-grow-0 p-0">
                    <UploadThumbnail
                        :file="file"
                        :path="[...path, idx]"
                        :question-id="questionId"
                        :object-url="objectUrls[file.file_ref]"
                        @remove="removeFile"
                    />
                </BCol>
            </BRow>
        </BContainer>
        <ValidationFeedback :validation="validation" />
        <BFormText v-if="helpText" :id="helpId">{{ helpText }}</BFormText>
    </FormGroup>
</template>

<script lang="ts" setup>
import { ref } from 'vue'

import { useFileUpload, useFormDataState } from '@/composables/question'
import {
    useAriaDescribedBy,
    useHelp,
    useId,
    useIsDisabled,
    usePath,
    useValidation,
} from '@/composables/question/elements'
import type { ElementPath, FileUploadElement, OptionsFile } from '@/types'

const { element, pathPrefix } = defineProps<{
    element: FileUploadElement
    pathPrefix: ElementPath
}>()

const path = usePath(pathPrefix, element)
const id = useId(path)
const { helpId, helpText } = useHelp(pathPrefix, element)
const ariaDescribedBy = useAriaDescribedBy([helpId.value])
const { questionId } = useFormDataState()
const toUpload = ref<File[]>([])
const { isUploading, model, objectUrls } = useFileUpload(pathPrefix, element, toUpload)
const isDisabled = useIsDisabled(isUploading)
const validation = useValidation(path)

async function removeFile(optionsFile: OptionsFile) {
    if (model.value) {
        model.value = model.value.filter((f) => f !== optionsFile)
    }
}
</script>
