import terser from "@rollup/plugin-terser";
import typescript from "@rollup/plugin-typescript";
import sass from "rollup-plugin-sass";
import { defineConfig } from "rollup";

export default defineConfig({
    input: "src/main.ts",
    output: {
        file: "js/main.js",
        format: "amd",
    },
    plugins: [typescript(), sass({ output: "css/styles.css" }), terser()],
});
