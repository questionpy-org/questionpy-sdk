<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <BModalOrchestrator />

    <BNavbar v-b-color-mode="inverseColorMode" :variant="inverseColorMode">
        <BNavbarBrand>
            <img alt="QuestionPy logo" class="d-inline-block logo pe-4" src="@/assets/logo.svg" />
            <span class="text-truncate">{{ appStateStore.displayPageTitle }}</span>
        </BNavbarBrand>
        <BButton
            class="d-flex align-items-center"
            pill
            size="lg"
            title="Switch color mode"
            :variant="inverseColorMode"
            @click="switchColorMode"
        >
            <i-mdi-white-balance-sunny v-if="mode === 'light'" />
            <i-mdi-weather-night v-else />
        </BButton>
    </BNavbar>

    <BContainer class="pt-4" fluid="md">
        <RouterView />
    </BContainer>
</template>

<script setup lang="ts">
import { useColorMode } from 'bootstrap-vue-next'
import { computed } from 'vue'
import type { BasicColorMode, BasicColorSchema } from '@vueuse/core'

import useAppStateStore from '@/stores/useAppStateStore'

const mode = useColorMode({ persist: true })
const appStateStore = useAppStateStore()

// Set document page title
appStateStore.$subscribe(() => {
    document.title = appStateStore.displayPageTitle
})

function invertColorSchema(schema: BasicColorSchema): BasicColorMode {
    const colorMode = schema === 'auto' ? mode.system.value : schema
    return colorMode === 'dark' ? 'light' : 'dark'
}

function switchColorMode() {
    mode.value = invertColorSchema(mode.value)
}

const inverseColorMode = computed(() => invertColorSchema(mode.value))
</script>

<style lang="scss" scoped>
.logo {
    height: 2rem;
}
</style>
