import terser from "@rollup/plugin-terser";
import typescript from "@rollup/plugin-typescript";
import sass from "rollup-plugin-sass";
import { defineConfig } from "rollup";
import path from "node:path"
import process from "node:process"

const jsOutputPath = process.env.QPY_DIST_JS ?? path.resolve(import.meta.dirname, "dist", "static", "js");
const cssOutputPath = process.env.QPY_DIST_CSS ?? path.resolve(import.meta.dirname, "dist", "static", "css");

export default defineConfig({
    input: "src/main.ts",
    output: {
        file: `${jsOutputPath}/main.js`,
        format: "amd",
    },
    plugins: [typescript(), sass({ output: `${cssOutputPath}/styles.css` }), terser()],
});
