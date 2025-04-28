/**
 * This file is part of the QuestionPy SDK. (https://questionpy.org)
 * The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
 * (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
 */

import { defineStore } from 'pinia'
import { computed } from 'vue'

import { useAttemptData, usePostAttempt, usePostAttemptRestart, usePostAttemptScore } from '@/queries/attempt'

import useAppStateStore from './useAppStateStore'

/** Provides attempt data. */
const useAttemptStore = defineStore('attemptData', () => {
    const { asyncStatus: dataAsyncStatus, state: dataState, refresh: dataRefresh } = useAttemptData()
    const { asyncStatus: postAsyncStatus, mutateAsync: postAttempt } = usePostAttempt()
    const { asyncStatus: postRestartAsyncStatus, mutateAsync: postRestart } = usePostAttemptRestart()
    const { asyncStatus: postScoreAsyncStatus, mutateAsync: postScore } = usePostAttemptScore()

    const { setError } = useAppStateStore()

    const isScored = computed(() => typeof dataState.value.data?.scoring_code === 'string')

    return {
        asyncStatus: computed(() =>
            [dataAsyncStatus, postAsyncStatus, postRestartAsyncStatus, postScoreAsyncStatus].every(
                ({ value }) => value === 'idle',
            )
                ? 'idle'
                : 'loading',
        ),

        // Attempt data
        attemptState: computed(() => dataState.value.data?.attempt_state),
        displayStatus: computed(() => {
            switch (dataState.value.data?.attempt_status) {
                case 'in_progress':
                    return 'In progress'
                case 'scored':
                    return 'Scored'
                case 'started':
                    return 'Started'
                default:
                    return ''
            }
        }),
        error: computed(() => dataState.value.error),
        iframeSrcDoc: computed(() => dataState.value.data?.attempt_html),
        renderErrors: computed(() => dataState.value.data?.render_errors ?? []),
        rescoreDisabled: computed(() => dataState.value.data?.attempt_status !== 'scored'),
        restartDisabled: computed(() => dataState.value.data?.attempt_status === 'started'),
        variant: computed(() => dataState.value.data?.variant),

        // ScoreModel
        displayScore: computed(() => (isScored.value ? dataState.value.data?.score?.toFixed(1) : null)),
        isScored,
        scoringCode: computed(() => (isScored.value ? dataState.value.data?.scoring_code : null)),
        scoringState: computed(() => (isScored.value ? dataState.value.data?.scoring_state : null)),

        /** Saves the attempt. */
        async save(formData: Record<string, unknown>) {
            try {
                await postAttempt(formData)
            } catch (err) {
                setError(err)
            }
        },

        /** Scores the attempt. */
        async score() {
            try {
                await postScore()
                await dataRefresh()
            } catch (err) {
                setError(err)
            }
        },

        /** Restarts the attempt. */
        async restart() {
            try {
                await postRestart()
                await dataRefresh()
            } catch (err) {
                setError(err)
            }
        },
    }
})

export default useAttemptStore
