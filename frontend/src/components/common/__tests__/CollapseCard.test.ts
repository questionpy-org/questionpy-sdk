/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { render, screen, waitFor } from '@testing-library/vue'

import CollapseCard from '@/components/common/CollapseCard.vue'

test('toggle button is visible', () => {
    render(CollapseCard, {
        slots: {
            default: '<div>card body</div>',
            'button-title': '<span>button title</span>',
        },
    })

    expect(screen.getByRole('button', { name: 'button title' })).toBeTruthy()
})

test('card is initially collapsed by default', () => {
    render(CollapseCard, {
        slots: {
            default: '<div>card body</div>',
            'button-title': '<span>button title</span>',
        },
    })

    expect(screen.getByText('card body')).not.toBeVisible()
})

test('card can be initially expanded', async () => {
    render(CollapseCard, {
        props: { expanded: true },
        slots: {
            default: '<div>card body</div>',
            'button-title': '<span>button title</span>',
        },
    })

    await waitFor(() => {
        expect(screen.getByText('card body')).toBeInTheDocument()
    })
})
