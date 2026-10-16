import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve, dirname, join } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const UPSTREAM = 'ec5e8986be294a187e4d257df883dccfabea1034';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = resolve(process.argv[2] ?? '../pose-animate');
const revision = execFileSync('git', ['-C', source, 'rev-parse', 'HEAD'], {encoding:'utf8'}).trim();
if (revision !== UPSTREAM) throw new Error('Expected pinned pose-animate commit ' + UPSTREAM + '; found ' + revision);
const input = join(source, 'dist', 'index.js');
const baseRuntime = readFileSync(input, 'utf8');
const presenterInput = join(source, 'dist', 'presenter.js');
const presenterRuntime = readFileSync(presenterInput, 'utf8');
if (/^\s*import\s/m.test(baseRuntime) || /\bimport\s*\(/.test(baseRuntime))
  throw new Error('Unexpected base renderer imports');
// TypeScript emits one relative dependency. Inline that compiled dependency so
// standalone file:// HTML has no unresolved module import or network fetch.
const presenterImport = /^import\s+\{\s*createSkiff\s*,\s*semanticPresentation\s*,\s*sequenceDuration\s*,\s*skiffSequences\s*\}\s+from\s+['"]\.\/index\.js['"];?\s*$/m;
if (!presenterImport.test(presenterRuntime)) throw new Error('Unexpected presenter dependency');
const presenterInline = presenterRuntime.replace(presenterImport, '');
if (/^\s*import\s/m.test(presenterInline) || /\bimport\s*\(/.test(presenterInline))
  throw new Error('Unexpected nested presenter imports');
const runtime = baseRuntime + '\n' + presenterInline;
if (/<\/script/i.test(runtime)) throw new Error('Unsafe HTML script terminator');
const { renderSvg, poses, semanticPresentation } = await import(pathToFileURL(input).href);
const { createSkiffPresenter } = await import(pathToFileURL(presenterInput).href);
if (typeof createSkiffPresenter !== 'function') throw new Error('Missing public presenter API');
const states = {
  ready:'ready', setup_pending:'waiting', unknown:'thinking',
  degraded:'warning', attention:'error'
};
const output=join(root,'src','host_welcome','assets');
mkdirSync(output,{recursive:true});
const hash=createHash('sha256').update(runtime).digest('hex');
writeFileSync(join(output,'pose_animate.js'), `// Generated from zog144/pose-animate @ ${UPSTREAM} (license: BSD-3-Clause OR GPL-3.0-only)
// Inline renderer + presenter SHA-256: ${hash}
// Do not hand-edit. Regenerate via scripts/sync-skiff.mjs.
` + runtime, 'utf8');
for (const [aggregate,state] of Object.entries(states)) {
  const present=semanticPresentation(state,'neutral');
  const svg=renderSvg({pose:{...poses[present.pose],face:present.face},
    palette:'blue',pulse:'none',phase:0});
  const squares=(svg.match(/id="skiff-limb-\d-segment-\d"/g)||[]).length;
  if (squares!==48 || !svg.includes('id="skiff-head"')) throw new Error('Invalid Skiff topology');
  writeFileSync(join(output,'skiff-'+aggregate+'.svg'), svg+'\n', 'utf8');
}
console.log('Generated canonical Skiff presenter and five state-specific SVGs from '+UPSTREAM);
