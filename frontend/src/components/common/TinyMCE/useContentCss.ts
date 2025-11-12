/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { storeToRefs } from 'pinia'
import { nextTick, ref, watch } from 'vue'

import useAppStateStore from '@/stores/useAppStateStore'

// There's no way of accessing compiled CSS directly apart from adjusting the Vite build pipeline. To keep things
// simple, we work with static CSS and properties.
import cssBaseBlock from './TinyMCEContent.css?raw'

const CSS_PROPERTIES = [
    '--bs-body-bg',
    '--bs-body-color',
    '--bs-body-font-size',
    '--bs-body-font-family',
    '--bs-font-monospace',
    '--bs-link-color',
    '--bs-link-hover-color',
    '--bs-body-line-height',
    '--bs-secondary-color',
    '--bs-border-color',
    '--bs-code-color',
]

function makeCssVarsBlock() {
    const cssProperties = CSS_PROPERTIES.map(
        (prop) => `${prop}: ${window.getComputedStyle(document.documentElement).getPropertyValue(prop).trim()};`,
    )
    return `:root { ${cssProperties.join('\n')} }`
}

/**
 * Provides TinyMCE-compatible content styles as two CSS blocks:
 * - `base`: static base styles.
 * - `vars`: reactive styles that update with the current color mode.
 *
 * @returns An object containing the static and dynamic CSS blocks.
 */
function useContentCss() {
    const { colorMode } = storeToRefs(useAppStateStore())
    const cssVarsBlock = ref(makeCssVarsBlock())

    watch(colorMode, async () => {
        await nextTick() // Give CSS properties time to recompute
        cssVarsBlock.value = makeCssVarsBlock()
    })

    return { base: cssBaseBlock, vars: cssVarsBlock }
}

export default useContentCss
