import '@testing-library/jest-dom/vitest'

import { config } from '@vue/test-utils'
import { createPinia } from 'pinia'

// Install Pinia globally for all tests
config.global.plugins = [createPinia()]
