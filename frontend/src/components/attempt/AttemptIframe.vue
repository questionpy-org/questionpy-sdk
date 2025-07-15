<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <iframe class="iframe" ref="iframeEl" :srcdoc="srcDoc" @load="onIframeLoad"></iframe>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { BasicColorMode } from '@vueuse/core'

import useAppStateStore from '@/stores/useAppStateStore'

defineProps<{ srcDoc: string }>()

const { colorMode } = storeToRefs(useAppStateStore())

const iframeEl = ref<HTMLIFrameElement | null>(null)

/** Retrieves form data from the iframe via `postMessage` communication. */
function getFormData(): Promise<Record<string, unknown>> {
    return new Promise((resolve, reject) => {
        if (iframeEl.value?.contentWindow) {
            const handleMessage = ({ data, origin }: MessageEvent) => {
                if (origin === window.origin && data?.type === 'FORM_DATA') {
                    window.removeEventListener('message', handleMessage)
                    resolve(data.formData)
                }
            }
            window.addEventListener('message', handleMessage)
            iframeEl.value.contentWindow.postMessage({ type: 'GET_FORM_DATA' })
        } else {
            reject(new Error('No iframe element'))
        }
    })
}

defineExpose({ getFormData })

// iframe color mode

function sendColorMode(mode: BasicColorMode) {
    if (iframeEl.value?.contentWindow) {
        iframeEl.value.contentWindow.postMessage({ type: 'COLOR_MODE_UPDATE', mode }, window.origin)
    }
}

function onIframeLoad() {
    sendColorMode(colorMode.value)
}

watch(colorMode, (newColorMode) => {
    sendColorMode(newColorMode)
})

// Handle iframe messages

function handleMessage({ data, origin }: MessageEvent) {
    if (origin === window.origin && data?.type === 'RESIZE_EVENT') {
        const newHeight = `${data.height + 1}px`
        if (iframeEl.value && iframeEl.value.style.height !== newHeight) {
            iframeEl.value.style.height = newHeight
        }
    }
}

onMounted(() => {
    window.addEventListener('message', handleMessage)
})

onBeforeUnmount(() => {
    window.removeEventListener('message', handleMessage)
})
</script>

<style lang="scss" scoped>
.iframe {
    background: transparent;
    border: 0;
    padding: 0;
    width: 100%;
    height: 0;
}
</style>
