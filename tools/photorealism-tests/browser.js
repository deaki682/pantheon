// Shared Chromium launch options for every harness.
// Priority: PR_CHROMIUM env → the remote sandbox's pinned build (if present)
// → playwright-core's own resolution (a local `npx playwright install chromium`).
const fs = require('fs');
const opts = {};
const pinned = process.env.PR_CHROMIUM || '/opt/pw-browsers/chromium';
if (fs.existsSync(pinned)) opts.executablePath = pinned;
module.exports = opts;
