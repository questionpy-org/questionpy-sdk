# QuestionPy SDK (Frontend)

A single-page application (SPA) for the QuestionPy SDK, developed using Vue.js.

## Development Setup

```sh
$ npm install
```

### Compile and Hot-Reload for Development

Start Vite dev server.

```sh
$ npm run dev
```

Run `questionpy-sdk` with reverse-proxying to the Vite development server.

```sh
$ USE_VITE_DEV_SERVER=true questionpy-sdk run examples/minimal
```

Use `VITE_DEV_SERVER` to override the default Vite dev server (`http://localhost:5173`).

### Type-Check, Compile and Minify for Production

```sh
$ npm run build
```

The production build is saved under `questionpy_sdk/webserver/static`.

### Run Tests with [Vitest](https://vitest.dev/)

```sh
$ npm run test
```

### Lint with [ESLint](https://eslint.org/)

```sh
$ npm run lint
```

### Format with [Prettier](https://prettier.io/)

Check if formatting is correct for all files.

```sh
$ npm run format-check
```

Auto-format all files.

```sh
$ npm run format
```

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) is needed to make the TypeScript language service aware of `.vue` types.

## Icon Set

[Material Design Icons](https://icon-sets.iconify.design/mdi/) licensed under [Apache License
2.0](https://github.com/google/material-design-icons/blob/master/LICENSE).
