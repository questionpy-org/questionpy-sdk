<!--
  This file is part of the QuestionPy SDK. (https://questionpy.org)
  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
-->

<template>
    <component :is="elementComponent" v-bind="elementProps" />
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import type { Component, ComponentInstance } from 'vue'

import type { FormElement } from '@/schema/options/types'

import CheckboxElement from './elements/CheckboxElement.vue'
import GeneratedIdElement from './elements/GeneratedIdElement.vue'
import GroupElement from './elements/GroupElement.vue'
import HiddenElement from './elements/HiddenElement.vue'
import RadioGroupElement from './elements/RadioGroupElement.vue'
import RepetitionElement from './elements/RepetitionElement.vue'
import SelectElement from './elements/SelectElement.vue'
import StaticTextElement from './elements/StaticTextElement.vue'
import TextAreaElement from './elements/TextAreaElement.vue'
import TextInputElement from './elements/TextInputElement.vue'

const props = defineProps<{
    disabled: boolean
    element: FormElement
    pathPrefix: string[]
}>()

const componentsMap = {
    checkbox: CheckboxElement,
    id: GeneratedIdElement,
    group: GroupElement,
    hidden: HiddenElement,
    radio_group: RadioGroupElement,
    repetition: RepetitionElement,
    select: SelectElement,
    static_text: StaticTextElement,
    textarea: TextAreaElement,
    input: TextInputElement,
} satisfies Record<FormElement['kind'], Component>

const elementComponent = computed(() => componentsMap[props.element.kind])
const elementProps = props as ComponentInstance<typeof elementComponent.value>['$props']
</script>
