// build-standalone.mjs — inline everything into ONE offline HTML file.
//
//   node tools/build-standalone.mjs   →   dist/metastrip.html
//
// This is the sellable, walk-away artifact: a single self-contained file the
// buyer double-clicks. It runs from file:// with no server, no network, no
// build tooling on their side. The extension itself needs no build step — this
// is only for the downloadable version. (Nothing here changes the extension.)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

let html = read('tool.html');
const css = read('tool.css');
const scripts = ['src/strip.js', 'src/exif.js', 'src/zip.js', 'src/app.js'].map(read);
const iconB64 = fs.readFileSync(path.join(ROOT, 'icons/icon48.png')).toString('base64');

// inline the stylesheet
html = html.replace('<link rel="stylesheet" href="tool.css">', `<style>\n${css}\n</style>`);
// inline the brand icon as a data URI
html = html.replace('src="icons/icon48.png"', `src="data:image/png;base64,${iconB64}"`);
// replace the four external <script src> tags with one inlined bundle
html = html.replace(
  /\s*<script src="src\/strip\.js"><\/script>\s*<script src="src\/exif\.js"><\/script>\s*<script src="src\/zip\.js"><\/script>\s*<script src="src\/app\.js"><\/script>/,
  '\n  <script>\n' + scripts.join('\n') + '\n  </script>'
);

if (html.includes('src/strip.js') || html.includes('href="tool.css"')) {
  console.error('WARNING: some assets were not inlined — check tool.html markers.');
}

fs.mkdirSync(path.join(ROOT, 'dist'), { recursive: true });
const out = path.join(ROOT, 'dist', 'metastrip.html');
fs.writeFileSync(out, html);
console.log(`Wrote ${path.relative(ROOT, out)} (${(html.length / 1024).toFixed(1)} KB, fully self-contained)`);
