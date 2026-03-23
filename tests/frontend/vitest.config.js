import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: [resolve(__dirname, 'setup.js')],
    include: ['unit/**/*.test.js', 'integration/**/*.test.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: resolve(__dirname, 'coverage'),
      include: [resolve(__dirname, '../../static/js/modules/**/*.js')]
    },
    testTimeout: 10000,
    hookTimeout: 10000
  }
});
