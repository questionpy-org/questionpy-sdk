<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <div :class="{ maximized: isMaximized }">
        <div v-if="isMaximized">
            <IconButton variant="link" :iconComponent="IMdiFullscreenExit" @click="isMaximized = false">
                Return question to normal size
            </IconButton>
        </div>
        <div v-else>
            <IconButton variant="link" :iconComponent="IMdiFullscreen" @click="isMaximized = true"
                >Maximize question</IconButton
            >
        </div>

        <iframe class="iframe" ref="iframeEl" :srcdoc="srcDoc" @load="onIframeLoad"></iframe>
    </div>
</template>

<script setup lang="ts">
import IMdiFullscreen from '~icons/mdi/fullscreen'
import IMdiFullscreenExit from '~icons/mdi/fullscreen-exit'
import { storeToRefs } from 'pinia'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { BasicColorMode } from '@vueuse/core'

import useAppStateStore from '@/stores/useAppStateStore'

defineProps<{ srcDoc: string }>()

const { colorMode } = storeToRefs(useAppStateStore())

const iframeEl = ref<HTMLIFrameElement | null>(null)

const isMaximized = ref(false)
watch(isMaximized, async (newValue) => {
    if (!iframeEl.value) {
        return
    }
    if (newValue) {
        // We've entered maximized mode.
        iframeEl.value.style.height = '100%'
    } else {
        // We've exited it.
        iframeEl.value.style.removeProperty('height')
    }

    iframeEl.value.contentWindow?.postMessage({
        type: 'UPDATE_DISPLAY_MODE',
        newDisplayMode: newValue ? 'maximized' : 'default',
    })
})

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
    if (isMaximized.value) {
        // If the question is maximized, we don't care how large its content is, the container is always as large as it
        // can be.
        return
    }

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
    height: 100%;
}

.maximized {
    position: fixed;
    box-sizing: border-box;
    width: 100vw;
    height: 100vw;
    top: 0;
    left: 0;
    background-color: var(--bs-body-bg);
    z-index: 100;
}
</style>
