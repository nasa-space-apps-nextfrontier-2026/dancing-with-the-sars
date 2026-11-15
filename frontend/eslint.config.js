import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'
export default tseslint.config(
  { ignores: ['dist','node_modules'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  { files: ['**/*.{ts,tsx}'], plugins: { 'react-hooks': reactHooks },
    languageOptions: { globals: globals.browser },
    rules: reactHooks.configs.recommended.rules },
  // landing scene is plain browser JS (src/features/landing/landingScene.js)
  { files: ['src/**/*.js'], languageOptions: { globals: globals.browser, sourceType: 'module' } }
)
