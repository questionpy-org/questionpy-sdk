/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import {
    areFormDataObjIdentical,
    createFormDataValues,
    getElementName,
    getErrorKey,
    getFormData,
    hasEditableElements,
} from '@/composables/question/formDataUtils'
import type {
    CheckboxElement,
    FormElement,
    GeneratedIdElement,
    GroupElement,
    HiddenElement,
    RadioGroupElement,
    RepetitionElement,
    SelectElement,
    TextInputElement,
} from '@/types'

import options from './options'

test('getElementName', () => {
    expect(getElementName(['general', 'foo', 'bar'])).toBe('general[foo][bar]')
})

test('getErrorKey (general)', () => {
    expect(getErrorKey(['general', 'a', '2', 'c'])).toBe('a.1.c')
})

test('getErrorKey (section)', () => {
    expect(getErrorKey(['section', '3', 'field'])).toBe('section.2.field')
})

test('getErrorKey (mixed parts)', () => {
    expect(getErrorKey(['section', 'a', '2', 'b', '3'])).toBe('section.a.1.b.2')
})

test('createFormDataValues (checkbox)', () => {
    const data = {}
    const checkbox = {
        kind: 'checkbox',
        name: 'chk',
        selected: true,
        left_label: null,
        right_label: null,
        required: false,
        disable_if: [],
        hide_if: [],
        help: null,
    } satisfies CheckboxElement
    createFormDataValues(data, [checkbox], ['general'])
    expect(data).toEqual({ 'general[chk]': true })
})

test('createFormDataValues (select single)', () => {
    const data = {}
    const select = {
        kind: 'select',
        name: 'my_select',
        label: '',
        multiple: false,
        options: [
            { label: 'Opt 1', value: 'OPT_1', selected: false },
            { label: 'Opt 2', value: 'OPT_2', selected: true },
        ],
        required: false,
        disable_if: [],
        hide_if: [],
        help: null,
    } satisfies SelectElement
    createFormDataValues(data, [select], ['general'])
    expect(data).toEqual({ 'general[my_select]': 'OPT_2' })
})

test('createFormDataValues (select multiple)', () => {
    const data = {}
    const select = {
        kind: 'select',
        name: 'my_select_multi',
        label: '',
        multiple: true,
        options: [
            { label: 'Opt 1', value: 'OPT_1', selected: true },
            { label: 'Opt 2', value: 'OPT_2', selected: false },
            { label: 'Opt 3', value: 'OPT_3', selected: true },
        ],
        required: false,
        disable_if: [],
        hide_if: [],
        help: null,
    } satisfies SelectElement
    createFormDataValues(data, [select], ['general'])
    expect(data).toEqual({ 'general[my_select_multi]': ['OPT_1', 'OPT_3'] })
})

test('createFormDataValues (input)', () => {
    const data = {}
    const input = {
        kind: 'input',
        name: 'input',
        label: '',
        required: false,
        default: 'default text',
        placeholder: null,
        disable_if: [],
        hide_if: [],
        help: null,
    } satisfies TextInputElement
    createFormDataValues(data, [input], ['general'])
    expect(data).toEqual({ 'general[input]': 'default text' })
})

test('createFormDataValues (hidden)', () => {
    const data = {}
    const hidden = {
        kind: 'hidden',
        name: 'my_hidden',
        value: 'foo',
        disable_if: [],
        hide_if: [],
    } satisfies HiddenElement
    createFormDataValues(data, [hidden], ['general'])
    expect(data).toEqual({ 'general[my_hidden]': 'foo' })
})

test('createFormDataValues (group)', () => {
    const data = {}
    const group = {
        kind: 'group',
        name: 'name_group',
        label: '',
        elements: [
            {
                kind: 'input',
                name: 'first_name',
                label: '',
                required: false,
                default: '',
                placeholder: null,
                disable_if: [],
                hide_if: [],
                help: null,
            },
            {
                kind: 'input',
                name: 'last_name',
                label: '',
                required: false,
                default: '',
                placeholder: null,
                disable_if: [],
                hide_if: [],
                help: null,
            },
        ],
        disable_if: [],
        hide_if: [],
        help: null,
    } satisfies GroupElement
    createFormDataValues(data, [group], ['general'])
    expect(data).toEqual({
        'general[name_group][first_name]': '',
        'general[name_group][last_name]': '',
    })
})

test('createFormDataValues (repetition)', () => {
    const data = {}
    const repetition = {
        kind: 'repetition',
        name: 'my_repetition',
        initial_repetitions: 2,
        minimum_repetitions: 1,
        increment: 1,
        button_label: null,
        elements: [
            {
                kind: 'id',
                name: 'id',
            },
            {
                kind: 'select',
                name: 'role',
                label: '',
                multiple: false,
                options: [],
                required: false,
                disable_if: [],
                hide_if: [],
                help: null,
            },
            {
                kind: 'group',
                name: 'name',
                label: '',
                elements: [
                    {
                        kind: 'input',
                        name: 'first_name',
                        label: '',
                        required: false,
                        default: 'Jane',
                        placeholder: null,
                        disable_if: [],
                        hide_if: [],
                        help: null,
                    },
                    {
                        kind: 'input',
                        name: 'last_name',
                        label: '',
                        required: false,
                        default: '',
                        placeholder: null,
                        disable_if: [],
                        hide_if: [],
                        help: null,
                    },
                ],
                disable_if: [],
                hide_if: [],
                help: null,
            },
        ],
    } satisfies RepetitionElement
    createFormDataValues(data, [repetition], ['general'])
    expect(data).toEqual({
        'general[my_repetition][1][id]': expect.stringMatching(/^[a-f\d-]+$/),
        'general[my_repetition][1][role]': '',
        'general[my_repetition][1][name][first_name]': 'Jane',
        'general[my_repetition][1][name][last_name]': '',
        'general[my_repetition][2][id]': expect.stringMatching(/^[a-f\d-]+$/),
        'general[my_repetition][2][role]': '',
        'general[my_repetition][2][name][first_name]': 'Jane',
        'general[my_repetition][2][name][last_name]': '',
    })
})

test('createFormDataValues (existing key skipped)', () => {
    const data = { 'general[input]': 'existing' }
    const input = {
        kind: 'input',
        name: 'input',
        label: '',
        required: false,
        default: 'default text',
        placeholder: null,
        disable_if: [],
        hide_if: [],
        help: null,
    } satisfies TextInputElement
    createFormDataValues(data, [input], ['general'])
    expect(data).toEqual({ 'general[input]': 'existing' })
})

test('createFormDataValues (radio group)', () => {
    const data = {}
    const radioGroup = {
        kind: 'radio_group',
        name: 'radio',
        label: '',
        options: [
            { label: 'Radio 1', value: 'RADIO_1', selected: false },
            { label: 'Radio 2', value: 'RADIO_2', selected: true },
        ],
        required: false,
        disable_if: [],
        hide_if: [],
        help: null,
    } satisfies RadioGroupElement
    createFormDataValues(data, [radioGroup], ['general'])
    expect(data).toEqual({ 'general[radio]': 'RADIO_2' })
})

test('createFormDataValues (generated ID)', () => {
    const data = {}
    const idElement = {
        kind: 'id',
        name: 'id',
    } satisfies GeneratedIdElement
    createFormDataValues(data, [idElement], ['general'])
    expect(data).toEqual({ 'general[id]': expect.stringMatching(/^[a-f\d-]+$/) })
})

test('getFormData', async () => {
    expect(getFormData(options, {})).toStrictEqual({
        'general[input]': 'default text',
        'general[chk]': false,
        'general[radio]': 'RADIO_2',
        'general[my_select]': 'OPT_2',
        'general[my_select_multi]': ['OPT_1', 'OPT_3'],
        'general[my_hidden]': 'foo',
        'general[my_repetition][1][id]': expect.stringMatching(/^[a-f\d-]+$/),
        'general[my_repetition][1][role]': 'OPT_1',
        'general[my_repetition][1][name][first_name]': 'Jane',
        'general[my_repetition][1][name][last_name]': '',
        'general[my_repetition][2][id]': expect.stringMatching(/^[a-f\d-]+$/),
        'general[my_repetition][2][role]': 'OPT_1',
        'general[my_repetition][2][name][first_name]': 'Jane',
        'general[my_repetition][2][name][last_name]': '',
        'general[has_name]': false,
        'general[name_group][first_name]': '',
        'general[name_group][last_name]': '',
        'another_section[some_input]': '',
    })
})

test('getFormData (with initial data)', async () => {
    const initialData = {
        'general[my_repetition][1][id]': 'fb79662e-1e2b-46d8-9655-3db4ecbbfab5',
        'general[my_repetition][1][role]': 'OPT_3',
        'general[my_repetition][1][name][first_name]': 'John',
        'general[my_repetition][1][name][last_name]': 'Doe',
    }

    expect(getFormData(options, initialData)).toStrictEqual({
        'general[input]': 'default text',
        'general[chk]': false,
        'general[radio]': 'RADIO_2',
        'general[my_select]': 'OPT_2',
        'general[my_select_multi]': ['OPT_1', 'OPT_3'],
        'general[my_hidden]': 'foo',
        'general[my_repetition][1][id]': 'fb79662e-1e2b-46d8-9655-3db4ecbbfab5',
        'general[my_repetition][1][role]': 'OPT_3',
        'general[my_repetition][1][name][first_name]': 'John',
        'general[my_repetition][1][name][last_name]': 'Doe',
        'general[has_name]': false,
        'general[name_group][first_name]': '',
        'general[name_group][last_name]': '',
        'another_section[some_input]': '',
    })
})

test('areFormDataObjIdentical (identical objects)', () => {
    const a = { a: '1', b: true, c: ['x', 'y'] }
    const b = { a: '1', b: true, c: ['x', 'y'] }
    expect(areFormDataObjIdentical(a, b)).toBe(true)
})

test('areFormDataObjIdentical (different string value)', () => {
    const a = { a: '1' }
    const b = { a: '2' }
    expect(areFormDataObjIdentical(a, b)).toBe(false)
})

test('areFormDataObjIdentical (different boolean value)', () => {
    const a = { b: true }
    const b = { b: false }
    expect(areFormDataObjIdentical(a, b)).toBe(false)
})

test('areFormDataObjIdentical (arrays same order)', () => {
    const a = { c: ['x', 'y'] }
    const b = { c: ['x', 'y'] }
    expect(areFormDataObjIdentical(a, b)).toBe(true)
})

test('areFormDataObjIdentical (arrays different order)', () => {
    const a = { c: ['x', 'y'] }
    const b = { c: ['y', 'x'] }
    expect(areFormDataObjIdentical(a, b)).toBe(false)
})

test('areFormDataObjIdentical (arrays different length)', () => {
    const a = { c: ['x'] }
    const b = { c: ['x', 'y'] }
    expect(areFormDataObjIdentical(a, b)).toBe(false)
})

test('areFormDataObjIdentical (different keys)', () => {
    const a = { a: '1' }
    const b = { b: '1' }
    expect(areFormDataObjIdentical(a, b)).toBe(false)
})

test('hasEditableElements (editable input)', () => {
    const elements = [
        {
            kind: 'input',
            name: 'input',
            label: '',
            required: false,
            default: '',
            placeholder: null,
            disable_if: [],
            hide_if: [],
            help: null,
        },
    ] satisfies FormElement[]
    expect(hasEditableElements(elements)).toBe(true)
})

test('hasEditableElements (non-editable static_text)', () => {
    const elements = [
        {
            kind: 'static_text',
            name: 'text',
            label: '',
            text: '',
            disable_if: [],
            hide_if: [],
            help: null,
        },
    ] satisfies FormElement[]
    expect(hasEditableElements(elements)).toBe(false)
})

test('hasEditableElements (group with editable)', () => {
    const elements = [
        {
            kind: 'group',
            name: 'group',
            label: '',
            elements: [
                {
                    kind: 'input',
                    name: 'input',
                    label: '',
                    required: false,
                    default: '',
                    placeholder: null,
                    disable_if: [],
                    hide_if: [],
                    help: null,
                },
            ],
            disable_if: [],
            hide_if: [],
            help: null,
        },
    ] satisfies FormElement[]
    expect(hasEditableElements(elements)).toBe(true)
})

test('hasEditableElements (group with non-editable)', () => {
    const elements = [
        {
            kind: 'group',
            name: 'group',
            label: '',
            elements: [
                {
                    kind: 'static_text',
                    name: 'text',
                    label: '',
                    text: '',
                    disable_if: [],
                    hide_if: [],
                    help: null,
                },
            ],
            disable_if: [],
            hide_if: [],
            help: null,
        },
    ] satisfies FormElement[]
    expect(hasEditableElements(elements)).toBe(false)
})

test('hasEditableElements (repetition with non-editable)', () => {
    const elements = [
        {
            kind: 'repetition',
            name: 'my_repetition',
            initial_repetitions: 1,
            minimum_repetitions: 1,
            increment: 1,
            button_label: null,
            elements: [
                {
                    kind: 'static_text',
                    name: 'text',
                    label: '',
                    text: '',
                    disable_if: [],
                    hide_if: [],
                    help: null,
                },
            ],
        },
    ] satisfies FormElement[]
    expect(hasEditableElements(elements)).toBe(true)
})

test('hasEditableElements (mix of elements)', () => {
    const elements = [
        {
            kind: 'static_text',
            name: 'text',
            label: '',
            text: '',
            disable_if: [],
            hide_if: [],
            help: null,
        },
        {
            kind: 'group',
            name: 'group',
            label: '',
            elements: [
                {
                    kind: 'input',
                    name: 'input',
                    label: '',
                    required: false,
                    default: '',
                    placeholder: null,
                    disable_if: [],
                    hide_if: [],
                    help: null,
                },
            ],
            disable_if: [],
            hide_if: [],
            help: null,
        },
        {
            kind: 'hidden',
            name: 'hidden',
            value: 'foo',
            disable_if: [],
            hide_if: [],
        },
    ] satisfies FormElement[]
    expect(hasEditableElements(elements)).toBe(true)
})

test('hasEditableElements (empty array)', () => {
    expect(hasEditableElements([])).toBe(false)
})

test('hasEditableElements (all non-editable)', () => {
    const elements = [
        {
            kind: 'hidden',
            name: 'hidden',
            value: 'foo',
            disable_if: [],
            hide_if: [],
        },
        {
            kind: 'id',
            name: 'id',
        },
        {
            kind: 'static_text',
            name: 'text',
            label: '',
            text: '',
            disable_if: [],
            hide_if: [],
            help: null,
        },
    ] satisfies FormElement[]
    expect(hasEditableElements(elements)).toBe(false)
})
