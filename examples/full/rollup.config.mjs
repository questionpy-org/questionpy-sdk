import terser from "@rollup/plugin-terser";
import typescript from "@rollup/plugin-typescript";
import sass from "rollup-plugin-sass";
import { defineConfig } from "rollup";

export default defineConfig({
    input: "src/main.ts",
    output: {
        file: `${process.env.QPY_DIST_JS}/main.js`,
        format: "amd",
    },
    plugins: [typescript(), sass({ output: `${process.env.QPY_DIST_CSS}/styles.css` }), terser()],
});
