<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <div class="wrapper bg-dark-subtle">
        <div class="thumbnail">
            <BImg v-if="isDisplayableImage" :alt="file.filename" :src="imageSrc" class="image" />
            <IMdiFile v-else class="image" />
            <samp class="filename text-truncate">{{ file.filename }}</samp>
        </div>
        <ActionButton
            v-if="isOptionsFile(file)"
            :icon-component="IMdiDelete"
            @click="emit('remove', file)"
            class="remove-btn"
            label="Remove file"
            variant="danger"
            size="sm"
        />
    </div>
</template>

<script lang="ts" setup>
import IMdiDelete from '~icons/mdi/delete'
import { computed } from 'vue'

import { isBrowserDisplayable } from '@/composables/question/useFileUpload'
import { API_BASE } from '@/queries'
import { isOptionsFile } from '@/types/typeUtils'
import type { ElementPath, OptionsFile } from '@/types'

const { file, questionId, objectUrl, path } = defineProps<{
    file: OptionsFile
    questionId: string
    /** An optional object URL to show a temporary thumbnail while uploading. */
    objectUrl?: string
    path: ElementPath
}>()

const emit = defineEmits<{
    remove: [OptionsFile]
}>()

const isDisplayableImage = computed(() => isBrowserDisplayable(file.mime_type))

const makeImageSrc = () =>
    objectUrl ?? `${API_BASE}question/${questionId}/file/${encodeURIComponent(path.join('.'))}/${file.file_ref}`

const imageSrc = computed(() => (isDisplayableImage.value ? makeImageSrc() : undefined))
</script>

<style lang="scss" scoped>
.wrapper {
    --thumbnail-padding: #{$spacer * 0.2};
    --thumbnail-size: 5rem;
    position: relative;
    padding: var(--thumbnail-padding);
    background-color: var(--bs-pink);
    border: var(--bs-border-width) solid var(--bs-border-color);
    border-radius: var(--bs-border-radius);
    width: var(--thumbnail-size);
    height: var(--thumbnail-size);
    overflow: hidden;

    @include media-breakpoint-up('md') {
        --thumbnail-padding: #{$spacer * 0.25};
        --thumbnail-size: 7.5rem;
    }

    @include media-breakpoint-up('lg') {
        --thumbnail-size: 10rem;
    }

    :deep(.remove-btn) {
        position: absolute;
        right: $spacer * 0.5;
        top: $spacer * 0.5;
        visibility: hidden;
    }

    &:hover :deep(.remove-btn) {
        visibility: inherit;
    }

    .thumbnail {
        display: flex;
        flex-direction: column;
        flex: 1 0 auto;
        gap: $spacer * 0.25;
        width: 100%;
        height: 100%;

        > .image {
            width: 100%;
            height: 100%;
            min-height: 0;
            object-fit: cover;
        }
    }

    .filename {
        font-size: calc(var(--bs-body-font-size) * 0.8);
        flex: 0 0 auto;
    }
}
</style>
