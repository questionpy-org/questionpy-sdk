/// <reference types="vite/client" />
/// <reference types="unplugin-icons/types/vue" />
/// <reference types="unplugin-vue-router/client" />

// core-js/actual/regexp/escape
// https://github.com/DefinitelyTyped/DefinitelyTyped/blob/8ddda4dc45ff72a23229a3d738239f2c18528117/types/core-js/index.d.ts#L63C1-L65C2
interface RegExpConstructor {
    escape(str: string): string
}
