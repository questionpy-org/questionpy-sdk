/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import type { Component } from 'vue'

import { assertNever, type FormElement } from '@/types'

import CheckboxElement from './CheckboxElement.vue'
import GeneratedIdElement from './GeneratedIdElement.vue'
import GroupElement from './GroupElement.vue'
import HiddenElement from './HiddenElement.vue'
import RadioGroupElement from './RadioGroupElement.vue'
import RepetitionElement from './RepetitionElement.vue'
import SelectElement from './SelectElement.vue'
import StaticTextElement from './StaticTextElement.vue'
import TextAreaElement from './TextAreaElement.vue'
import TextInputElement from './TextInputElement.vue'

/**
 * Maps an element `kind` property to a component.
 *
 * @param kind The element's `kind` property
 * @returns A Vue component
 */
function mapElementKindToComponent(kind: FormElement['kind']): Component {
    switch (kind) {
        case 'checkbox':
            return CheckboxElement
        case 'group':
            return GroupElement
        case 'hidden':
            return HiddenElement
        case 'id':
            return GeneratedIdElement
        case 'input':
            return TextInputElement
        case 'radio_group':
            return RadioGroupElement
        case 'repetition':
            return RepetitionElement
        case 'select':
            return SelectElement
        case 'static_text':
            return StaticTextElement
        case 'textarea':
            return TextAreaElement
        case 'file_upload':
        case 'wysiwyg_editor':
            // TODO: Implement.
            throw new Error('Form element not yet implemented: ' + kind)
        default:
            assertNever(kind)
    }
}

export { mapElementKindToComponent }
