/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { readFile } from 'node:fs/promises'
import path from 'node:path'

import { optionsSchema } from '@/schema/options'
import { getElementName, getFormData } from '@/stores/useOptionsFormDataStore/formDataUtils'

const data = await readFile(path.join(import.meta.dirname, 'options.json'))
const options = optionsSchema.parse(JSON.parse(data.toString()))

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

test('getElementName', () => {
    expect(getElementName(['general', 'foo', 'bar'])).toBe('general[foo][bar]')
})
