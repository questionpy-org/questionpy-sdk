<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <component :is="node" />
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import type { VNode } from 'vue'

import type { TemplateKwargs } from '@/types'

const PLACEHOLDER_REGEX = /({\w+})/g

const props = defineProps<{
    template: string
    values: TemplateKwargs
}>()

/**
 * Renders an array of strings into a sequence of `VNode`s and text separators.
 *
 * @example
 * // Returns: [<code>'A'</code>, ', ', <code>'B'</code>, ' and ', <code>'C'</code>]
 * renderStringArray(['A', 'B', 'C'])
 *
 * @param arrValue - The array of strings to render
 * @returns An array of VNodes and strings representing the formatted array output
 */
function renderStringArray(arrValue: string[]): (VNode | string)[] {
    const nodes: (VNode | string)[] = []

    if (arrValue.length > 0) {
        for (let i = 0; i < arrValue.length - 1; ++i) {
            // Add all but the last value,
            nodes.push(h('code', arrValue[i]))
            // each followed by a ', ', except for the second-to-last one, which is followed by ' and '.
            nodes.push(i < arrValue.length - 2 ? ', ' : ' and ')
        }

        // Add the last (or only) value.
        const lastValue = arrValue[arrValue.length - 1]
        nodes.push(h('code', lastValue))
    }

    return nodes
}

/**
 * Renders a template string with placeholders into a Vue `VNode` tree.
 *
 * @example
 * // Returns: <span>Result: <code>42</code> and <code>100</code></span>
 * renderTemplate("Result: {value1} and {value2}", {
 *   value1: "42",
 *   value2: "100"
 * })
 *
 * @param template - The template string containing `{placeholder}` segments
 * @param kwargs - An object mapping placeholder keys to `string` or `string[]` values
 * @returns A `VNode` representing the rendered template wrapped in a `<span>`
 * @throws {Error} When a placeholder in the template has no corresponding value in `kwargs`
 */
function renderTemplate(template: string, kwargs: TemplateKwargs): VNode {
    const children: (VNode | string)[] = []

    const tokens = template
        .split(PLACEHOLDER_REGEX)
        // Skip empty strings if placeholder is at template start/end
        .filter(Boolean)

    for (const token of tokens) {
        // Placeholder segment
        if (token.startsWith('{') && token.endsWith('}')) {
            const key = token.slice(1, -1)
            const value = kwargs[key]
            if (value === undefined) {
                throw new Error(`Missing value for placeholder '${key}'`)
            }
            if (Array.isArray(value)) {
                children.push(...renderStringArray(value))
            } else {
                children.push(h('code', value))
            }
        }
        // Text segment
        else {
            children.push(token)
        }
    }

    return h('span', children)
}

const node = computed(() => renderTemplate(props.template, props.values))
</script>
