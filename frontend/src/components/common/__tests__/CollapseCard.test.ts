/*
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { render, screen, waitFor } from '@testing-library/vue'

import CollapsibleCard from '@/components/common/CollapsibleCard.vue'

test('toggle button is visible', () => {
    render(CollapsibleCard, {
        slots: {
            default: '<div>card body</div>',
            'button-title': '<span>button title</span>',
        },
    })

    expect(screen.getByRole('button', { name: 'button title' })).toBeTruthy()
})

test('card is initially collapsed by default', () => {
    render(CollapsibleCard, {
        slots: {
            default: '<div>card body</div>',
            'button-title': '<span>button title</span>',
        },
    })

    expect(screen.getByText('card body')).not.toBeVisible()
})

test('card can be initially expanded', async () => {
    render(CollapsibleCard, {
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
