import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve, dirname, join } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const UPSTREAM = 'b7a6e3bdb15d0a15cc8b8cbc17e295dd472dc57a';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = resolve(process.argv[2] ?? '../pose-animate');
const revision = execFileSync('git', ['-C', source, 'rev-parse', 'HEAD'], {encoding:'utf8'}).trim();
if (revision !== UPSTREAM) throw new Error('Expected pinned pose-animate commit ' + UPSTREAM + '; found ' + revision);
const input = join(source, 'dist', 'index.js');
const runtime = readFileSync(input, 'utf8');
if (/^\s*import\s/m.test(runtime) || /\bimport\s*\(/.test(runtime)) throw new Error('Unexpected runtime imports');
const { createSkiff, renderSvg, poses, semanticPresentation } = await import(pathToFileURL(input).href);
if (typeof createSkiff !== 'function') throw new Error('Missing createSkiff');
const states = {
  ready:'ready', setup_pending:'waiting', unknown:'thinking',
  degraded:'warning', attention:'error'
};
const output=join(root,'src','host_welcome','assets');
mkdirSync(output,{recursive:true});
const hash=createHash('sha256').update(runtime).digest('hex');
writeFileSync(join(output,'pose_animate.js'), `// Generated from zog144/pose-animate @ ${UPSTREAM} (package license: MIT)
// Compiled module SHA-256: ${hash}
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
console.log('Generated canonical Skiff runtime and five state-specific SVGs from '+UPSTREAM);
