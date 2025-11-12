/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import 'tinymce' // TinyMCE uses a global, so need to import first!
// Required components
import 'tinymce/icons/default'
import 'tinymce/models/dom'
import 'tinymce/themes/silver'
// UI skin
import 'tinymce/skins/ui/oxide/skin.css'
// Plugins
import 'tinymce/plugins/advlist'
import 'tinymce/plugins/anchor'
import 'tinymce/plugins/autolink'
import 'tinymce/plugins/charmap'
import 'tinymce/plugins/code'
import 'tinymce/plugins/emoticons'
import 'tinymce/plugins/emoticons/js/emojis'
import 'tinymce/plugins/fullscreen'
import 'tinymce/plugins/help'
import 'tinymce/plugins/help/js/i18n/keynav/en.js'
import 'tinymce/plugins/image'
import 'tinymce/plugins/link'
import 'tinymce/plugins/lists'
import 'tinymce/plugins/media'
import 'tinymce/plugins/nonbreaking'
import 'tinymce/plugins/preview'
import 'tinymce/plugins/searchreplace'
import 'tinymce/plugins/table'
import 'tinymce/plugins/visualchars'
import 'tinymce/plugins/wordcount'

import { useDebounceFn } from '@vueuse/core'
import tinymce from 'tinymce'
import { onBeforeUnmount, onMounted, watch } from 'vue'
import type { Editor, RawEditorOptions as TineMCEOptions } from 'tinymce/tinymce'
import type { Ref } from 'vue'

import type { RichTextEditor } from '@/types'

import useContentCss from './useContentCss'

const PLUGINS = [
    'advlist',
    'anchor',
    'autolink',
    'charmap',
    'code',
    'fullscreen',
    'help',
    'image',
    'link',
    'lists',
    'media',
    'nonbreaking',
    'preview',
    'searchreplace',
    'table',
    'visualchars',
    'wordcount',
]

const TOOLBAR = [
    {
        name: 'history',
        items: ['undo', 'redo'],
    },
    {
        name: 'style',
        items: ['styles'],
    },
    {
        name: 'formatting',
        items: ['bold', 'italic', 'underline', 'strikethrough'],
    },
    {
        name: 'alignment',
        items: ['alignleft', 'aligncenter', 'alignright', 'alignjustify'],
    },
    {
        name: 'lists',
        items: ['bullist', 'numlist', 'outdent', 'indent'],
    },
    {
        name: 'insert',
        items: ['link', 'image', 'charmap'],
    },
]

interface UseTinyMCEInstanceOptions {
    /** A ref pointing to the HTML element where TinyMCE will be mounted. */
    targetElement: Ref<HTMLElement | undefined>
    /** Callback function invoked with a `RichTextEditor` object whenever the editor content changes. */
    onUpdate: (state: RichTextEditor) => void
    /** Optional initial editor state (default: empty). */
    initialState?: RichTextEditor
    /** Optional TinyMCE initialization options to merge with defaults. */
    tinyMCEOptions?: TineMCEOptions
}

/**
 * Composable for creating and managing a TinyMCE editor instance on a target element.
 *
 * @param options An object containing the composable options.
 * @returns The TinyMCE `Editor` instance, or `null` if it has not been initialized yet.
 */
function useTinyMCEInstance(options: UseTinyMCEInstanceOptions): Editor | null {
    const mergedOptions = {
        initialState: { text: '', files: [] },
        initOptions: {},
        ...options,
    }

    let editorInstance: Editor | null = null
    const contentCss = useContentCss()

    // As TinyMCE may fire frequent updates, we debounce model updates
    const debouncedUpdate = useDebounceFn(() => {
        if (editorInstance) {
            mergedOptions.onUpdate({ text: editorInstance.getContent(), files: [] })
        }
    }, 200)

    // TinyMCE initialization
    onMounted(() => {
        tinymce.init({
            target: mergedOptions.targetElement.value,
            plugins: PLUGINS,
            toolbar: TOOLBAR,

            height: 500,
            image_caption: true,

            // Use 'gpl' for self-hosting
            license_key: 'gpl',

            // Hide distracting self-promotion
            branding: false,
            promotion: false,

            // Prevent TinyMCE from dynamically loading any CSS
            content_css: false,
            skin: false,

            // Setup event handlers
            setup: (newEditorInstance) => {
                editorInstance = newEditorInstance

                newEditorInstance.on('init', () => {
                    if (editorInstance) {
                        // Inject content CSS into editor iframe
                        editorInstance.dom.styleSheetLoader.loadRawCss('BASE_CSS', contentCss.base)
                        editorInstance.dom.styleSheetLoader.loadRawCss('VARS_CSS', contentCss.vars.value)
                        // Set initial content
                        editorInstance.setContent(mergedOptions.initialState.text)
                    }
                })

                // Emit model updates on content change
                newEditorInstance.on('change keyup undo redo', () => {
                    debouncedUpdate()
                })
            },
            ...mergedOptions.tinyMCEOptions,
        })
    })

    // Update content CSS (on color mode change)
    watch(contentCss.vars, (newCssVars) => {
        if (editorInstance && editorInstance.dom) {
            editorInstance.dom.styleSheetLoader.unloadRawCss('VARS_CSS')
            editorInstance.dom.styleSheetLoader.loadRawCss('VARS_CSS', newCssVars)
        }
    })

    // Clean-up
    onBeforeUnmount(() => {
        if (editorInstance) {
            tinymce.remove(editorInstance)
        }
    })

    return editorInstance
}

export default useTinyMCEInstance
