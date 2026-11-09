// Hermetic script tests must not load the application Vite plugins.
export default { test: { include: ['tests/startup-script.test.ts', 'tests/local-package.test.ts'] } }
