/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import {
    areFormDataObjIdentical,
    createFormDataValues,
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

test('getErrorKey (general)', () => {
    expect(getErrorKey(['general', 'a', 1, 'c'])).toBe('a.1.c')
})

test('getErrorKey (section)', () => {
    expect(getErrorKey(['section', 2, 'field'])).toBe('section.2.field')
})

test('getErrorKey (mixed parts)', () => {
    expect(getErrorKey(['section', 'a', 1, 'b', 2])).toBe('section.a.1.b.2')
})

test('createFormDataValues (checkbox)', () => {
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
    expect(createFormDataValues([checkbox])).toEqual({ chk: true })
})

test('createFormDataValues (select single)', () => {
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
    expect(createFormDataValues([select])).toEqual({ my_select: 'OPT_2' })
})

test('createFormDataValues (select multiple)', () => {
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
    expect(createFormDataValues([select])).toEqual({ my_select_multi: ['OPT_1', 'OPT_3'] })
})

test('createFormDataValues (input)', () => {
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
    expect(createFormDataValues([input])).toEqual({ input: 'default text' })
})

test('createFormDataValues (hidden)', () => {
    const hidden = {
        kind: 'hidden',
        name: 'my_hidden',
        value: 'foo',
        disable_if: [],
        hide_if: [],
    } satisfies HiddenElement
    expect(createFormDataValues([hidden])).toEqual({ my_hidden: 'foo' })
})

test('createFormDataValues (group)', () => {
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
    expect(createFormDataValues([group])).toEqual({ name_group: { first_name: '', last_name: '' } })
})

test('createFormDataValues (repetition)', () => {
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
    expect(createFormDataValues([repetition])).toEqual({
        my_repetition: [
            {
                id: expect.stringMatching(/^[a-f\d-]+$/),
                role: '',
                name: {
                    first_name: 'Jane',
                    last_name: '',
                },
            },
            {
                id: expect.stringMatching(/^[a-f\d-]+$/),
                role: '',
                name: {
                    first_name: 'Jane',
                    last_name: '',
                },
            },
        ],
    })
})

test('createFormDataValues (existing key skipped)', () => {
    const data = { input: 'existing' }
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
    expect(createFormDataValues([input], data)).toEqual({ input: 'existing' })
})

test('createFormDataValues (radio group)', () => {
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
    expect(createFormDataValues([radioGroup])).toEqual({ radio: 'RADIO_2' })
})

test('createFormDataValues (generated ID)', () => {
    const idElement = {
        kind: 'id',
        name: 'id',
    } satisfies GeneratedIdElement
    expect(createFormDataValues([idElement])).toEqual({ id: expect.stringMatching(/^[a-f\d-]+$/) })
})

test('getFormData', async () => {
    expect(getFormData(options, {})).toStrictEqual({
        another_section: {
            some_input: '',
        },
        chk: false,
        has_name: false,
        input: 'default text',
        my_hidden: 'foo',
        my_repetition: [
            {
                id: expect.stringMatching(/^[a-f\d-]+$/),
                name: {
                    first_name: 'Jane',
                    last_name: '',
                },
                role: 'OPT_1',
            },
            {
                id: expect.stringMatching(/^[a-f\d-]+$/),
                name: {
                    first_name: 'Jane',
                    last_name: '',
                },
                role: 'OPT_1',
            },
        ],
        my_select: 'OPT_2',
        my_select_multi: ['OPT_1', 'OPT_3'],
        name_group: {
            first_name: '',
            last_name: '',
        },
        radio: 'RADIO_2',
    })
})

test('getFormData (with initial data)', async () => {
    const initialData = {
        my_repetition: [
            {
                id: 'fb79662e-1e2b-46d8-9655-3db4ecbbfab5',
                role: 'OPT_3',
                name: {
                    first_name: 'John',
                    last_name: 'Doe',
                },
            },
        ],
    }

    expect(getFormData(options, initialData)).toStrictEqual({
        another_section: {
            some_input: '',
        },
        chk: false,
        has_name: false,
        input: 'default text',
        my_hidden: 'foo',
        my_repetition: [
            {
                id: 'fb79662e-1e2b-46d8-9655-3db4ecbbfab5',
                role: 'OPT_3',
                name: {
                    first_name: 'John',
                    last_name: 'Doe',
                },
            },
        ],
        my_select: 'OPT_2',
        my_select_multi: ['OPT_1', 'OPT_3'],
        name_group: {
            first_name: '',
            last_name: '',
        },
        radio: 'RADIO_2',
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

test('areFormDataObjIdentical (nested identical objects)', () => {
    const a = { nested: { a: '1', b: true } }
    const b = { nested: { a: '1', b: true } }
    expect(areFormDataObjIdentical(a, b)).toBe(true)
})

test('areFormDataObjIdentical (nested different values)', () => {
    const a = { nested: { a: '1' } }
    const b = { nested: { a: '2' } }
    expect(areFormDataObjIdentical(a, b)).toBe(false)
})

test('areFormDataObjIdentical (nested different structure)', () => {
    const a = { nested: { a: '1' } }
    const b = { nested: { b: '1' } }
    expect(areFormDataObjIdentical(a, b)).toBe(false)
})

test('areFormDataObjIdentical (deeply nested objects)', () => {
    const a = { level1: { level2: { value: 'test' } } }
    const b = { level1: { level2: { value: 'test' } } }
    expect(areFormDataObjIdentical(a, b)).toBe(true)
})

test('areFormDataObjIdentical (arrays of nested objects)', () => {
    const a = { items: [{ id: 1 }, { id: 2 }] }
    const b = { items: [{ id: 1 }, { id: 2 }] }
    expect(areFormDataObjIdentical(a, b)).toBe(true)
})

test('areFormDataObjIdentical (arrays of nested objects different)', () => {
    const a = { items: [{ id: 1 }, { id: 2 }] }
    const b = { items: [{ id: 1 }, { id: 3 }] }
    expect(areFormDataObjIdentical(a, b)).toBe(false)
})

test('areFormDataObjIdentical (mixed nested structures)', () => {
    const a = {
        simple: 'value',
        nested: {
            array: ['1', '2', '3'],
            deep: { flag: true },
        },
    }
    const b = {
        simple: 'value',
        nested: {
            array: ['1', '2', '3'],
            deep: { flag: true },
        },
    }
    expect(areFormDataObjIdentical(a, b)).toBe(true)
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
