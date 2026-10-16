// Generated from zog144/pose-animate @ ec5e8986be294a187e4d257df883dccfabea1034 (license: BSD-3-Clause OR GPL-3.0-only)
// Inline renderer + presenter SHA-256: 750b6b82cd5e32f91a8718a50932b276584bdffb9a0b01c37b1750a33061f688
// Do not hand-edit. Regenerate via scripts/sync-skiff.mjs.
export const palettes = {
    blue: { body: '#32aae1', dark: '#1675b2', mid: '#1d91cc', light: '#55c8ee', tip: '#8ce5f5', eye: '#102a49', outline: '#123c60' },
    green: { body: '#3acb9b', dark: '#16866b', mid: '#22ae86', light: '#6de0b5', tip: '#a2edd2', eye: '#103c39', outline: '#12554e' },
    amber: { body: '#f5b73c', dark: '#b8781e', mid: '#db9428', light: '#ffcf70', tip: '#ffe4a5', eye: '#453016', outline: '#60401b' },
    red: { body: '#ef766d', dark: '#b33c4e', mid: '#dc5a61', light: '#ffa099', tip: '#ffc3b6', eye: '#491c30', outline: '#6c2836' },
    purple: { body: '#a78de9', dark: '#6348b8', mid: '#886acb', light: '#c0a9f5', tip: '#daceff', eye: '#241e4c', outline: '#40316f' },
    cyan: { body: '#45d9dd', dark: '#168caa', mid: '#1fb6c4', light: '#8beced', tip: '#c4f6f3', eye: '#133b50', outline: '#185c6e' }
};
// Clockwise: upper-left, upper-right, middle-right, lower-right,
// inner-lower-right, inner-lower-left, lower-left, middle-left.
// Head: 8 x 8 logical units, origin (0,0). All segment centres lie outside it.
const idleLimbs = [
    [[-1, 1], [-2, 0], [-3, -1], [-4, -2], [-5, -2], [-6, -3]],
    [[8, 1], [9, 0], [10, -1], [11, -2], [12, -2], [13, -3]],
    [[8, 3], [9, 3], [10, 2], [11, 2], [12, 1], [13, 1]],
    [[7, 8], [8, 9], [9, 10], [10, 11], [11, 11], [12, 12]],
    [[5, 8], [5, 9], [6, 10], [6, 11], [7, 12], [7, 13]],
    [[2, 8], [2, 9], [1, 10], [1, 11], [0, 12], [0, 13]],
    [[0, 8], [-1, 9], [-2, 10], [-3, 11], [-4, 11], [-5, 12]],
    [[-1, 4], [-2, 4], [-3, 5], [-4, 5], [-5, 6], [-6, 6]]
];
const cloneLimbs = (limbs) => limbs.map(limb => limb.map(([x, y]) => [x, y]));
/** A gentle hooked silhouette: distal squares curve back toward the body. */
export const SKIFF_LIMB_CURL = 0.14;
const curlDirections = [
    [1, .18], [-1, .18], [-.85, .8], [-.5, -.25], [-.8, -.55],
    [.8, -.55], [.5, -.25], [.85, .8]
];
const curlLimb = (limb, i) => {
    const [ax, ay] = limb[0];
    const [cx, cy] = curlDirections[i];
    return limb.map(([x, y], segment) => {
        const bend = Math.pow(Math.max(0, (segment - 2) / 3), 2);
        return [x + (ax - x) * SKIFF_LIMB_CURL * bend + cx * bend,
            y + (ay - y) * SKIFF_LIMB_CURL * bend + cy * bend];
    });
};
const pose = (face, overrides = [], foregroundTipLimb) => {
    const limbs = cloneLimbs(idleLimbs);
    for (const [index, coords] of overrides)
        limbs[index] = coords.map(([x, y]) => [x, y]);
    return { head: [0, 0], limbs: limbs.map(curlLimb), face,
        ...(foregroundTipLimb === undefined ? {} : { foregroundTipLimb }) };
};
export const poses = {
    idle: pose('open'),
    greet: pose('happy', [[1, [[8, 1], [9, 0], [10, -1], [10, -2], [9, -3], [9, -4]]]]),
    wave: pose('happy', [[1, [[8, 1], [9, 0], [10, -1], [11, -1], [11, -2], [10, -3]]]]),
    listen: pose('focused', [[2, [[8, 3], [9, 2], [10, 2], [11, 1], [12, 1], [12, 0]]]]),
    // Aim at the left of the mouth/chin, not upward at the nose.
    // These points precede shared curling: the actual resting tip is ~[2.57, 5.64].
    ponder: pose('focused', [[4, [[5, 8], [5.8, 8], [5.25, 7], [4.7, 6.25], [3.8, 5.85], [3.1, 5.9]]]], 4),
    present: pose('happy', [[2, [[8, 3], [9, 3], [10, 3], [11, 3], [12, 3], [13, 3]]]]),
    celebrate: pose('happy', [[0, [[-1, 1], [-2, 0], [-3, -1], [-4, -2], [-5, -3], [-6, -4]]], [1, [[8, 1], [9, 0], [10, -1], [11, -2], [12, -3], [13, -4]]], [6, [[0, 8], [-1, 9], [-2, 10], [-3, 11], [-4, 12], [-5, 13]]]]),
    droop: pose('concerned', [
        [0, [[-1, 1], [-2, 2], [-3, 3], [-3, 4], [-3, 5], [-2, 6]]],
        [1, [[8, 1], [9, 2], [10, 3], [10, 4], [10, 5], [9, 6]]],
        [2, [[8, 3], [9, 4], [10, 5], [11, 6], [11, 7], [11, 8]]],
        [7, [[-1, 4], [-2, 5], [-3, 6], [-4, 7], [-4, 8], [-4, 9]]]
    ]),
    recover: pose('happy', [
        [0, [[-1, 1], [-2, 0], [-3, -1], [-3, -2], [-2, -3], [-1, -4]]],
        [1, [[8, 1], [9, 0], [10, -1], [10, -2], [9, -3], [8, -4]]],
        [2, [[8, 3], [9, 2], [10, 1], [11, 0], [12, 0], [13, -1]]],
        [7, [[-1, 4], [-2, 3], [-3, 2], [-4, 1], [-5, 0], [-5, -1]]]
    ])
};
export function validatePose(p) {
    if (p.limbs.length !== 8 || p.limbs.some(l => l.length !== 6))
        throw new Error('Skiff requires eight six-segment limbs');
    if (![...p.head, ...p.limbs.flatMap(l => l.flat())].every(Number.isFinite))
        throw new Error('Pose has non-finite coordinate');
    if (p.foregroundTipLimb !== undefined && (!Number.isInteger(p.foregroundTipLimb) || p.foregroundTipLimb < 0 || p.foregroundTipLimb > 7))
        throw new Error('Invalid foreground tip limb');
}
export function interpolate(from, to, progress) {
    validatePose(from);
    validatePose(to);
    const t = Math.min(1, Math.max(0, Number.isFinite(progress) ? progress : 0));
    const mix = (a, b) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
    return { head: mix(from.head, to.head), limbs: from.limbs.map((l, i) => l.map((s, j) => mix(s, to.limbs[i][j]))), face: t < 0.5 ? from.face : to.face, ...((t < .5 ? from.foregroundTipLimb : to.foregroundTipLimb) === undefined ? {} : { foregroundTipLimb: t < .5 ? from.foregroundTipLimb : to.foregroundTipLimb }) };
}
/** Every limb travels as a six-segment articulated wave, rather than a rigid arm.
 *  Sampling is clock-independent, reproducible and quantized to twelve steps/sec.
 *  Headward segments stay close to their original anchor, while later squares
 *  receive delayed displacement. Rectangles remain axis aligned at all times.
 */
export function samplePose(name, seconds = 0, motion = true) {
    if (!Object.hasOwn(poses, name))
        throw new Error('Unknown Skiff pose');
    const base = poses[name];
    if (!motion)
        return base;
    const time = Math.floor(Math.max(0, Number.isFinite(seconds) ? seconds : 0) * 12) / 12;
    const tau = Math.PI * 2;
    const wave = (rate, delay = 0) => Math.sin(tau * rate * time - delay);
    let headBob = .1 * wave(.16);
    const moving = base.limbs.map((limb, i) => limb.map(([x, y], j) => {
        const reach = Math.pow(j / 5, 1.55); // proximal joint nearly fixed
        const delay = j * .16; // wave arrives later at the tip
        const small = .07 * reach * wave(.18, i * .8 + delay);
        let dx = small, dy = .025 * reach * wave(.2, i * .9 + delay);
        // A transverse wave propagates down the arm without rotating any squares.
        const [ax, ay] = limb[0];
        const length = Math.hypot(x - ax, y - ay) || 1;
        const transverse = .085 * reach * wave(.42, i * .52 + delay * 1.8);
        dx += -(y - ay) / length * transverse;
        dy += (x - ax) / length * transverse;
        switch (name) {
            case 'greet':
                if (i === 1) {
                    dx += reach * 1.15 * wave(.65, delay);
                    dy -= reach * (.25 + .2 * wave(.65, delay + .8));
                }
                if (i === 0) {
                    dx -= reach * .28 * wave(.65, delay + .4);
                    dy += reach * .12 * wave(.65, delay);
                }
                break;
            case 'wave':
                if (i === 1) {
                    dx += reach * 2.15 * wave(.95, delay);
                    dy += reach * .38 * wave(.95, delay + Math.PI / 2);
                }
                if (i === 0 || i === 2) {
                    dx -= reach * .36 * wave(.95, delay + .5);
                    dy += reach * .13 * wave(.95, delay);
                }
                if (i === 6) {
                    dy += reach * .1 * wave(.45, delay);
                }
                break;
            case 'listen':
                if (i === 2) {
                    dx += reach * .75 * wave(.55, delay);
                    dy -= reach * (.45 + .32 * wave(.55, delay + .6));
                }
                if (i === 7) {
                    dx -= reach * .5 * wave(.55, delay + 1);
                    dy -= reach * .24 * wave(.55, delay);
                }
                if (i === 4 || i === 5) {
                    dy += reach * .12 * wave(.4, delay + i);
                }
                break;
            case 'ponder':
                // Restrained fingertip movement stays beside Skiff's left chin.
                if (i === 4) {
                    dx += reach * .22 * wave(.43, delay);
                    dy += reach * .14 * wave(.43, delay + .8);
                }
                if (i === 5) {
                    dx += reach * .34 * wave(.43, delay + 1);
                    dy -= reach * .26 * wave(.43, delay + .5);
                }
                if (i === 1) {
                    dy += reach * .13 * wave(.43, delay + .4);
                }
                break;
            case 'present':
                if (i === 2) {
                    dx += reach * (.55 + .55 * wave(.55, delay));
                    dy -= reach * .22 * wave(.55, delay);
                }
                if (i === 3) {
                    dx += reach * .35 * wave(.55, delay + .9);
                    dy -= reach * .14 * wave(.55, delay);
                }
                if (i === 7) {
                    dx -= reach * .3 * wave(.55, delay);
                }
                break;
            case 'celebrate':
                if ([0, 1, 3, 4, 5, 6].includes(i)) {
                    const offset = (i % 2) * Math.PI * .65;
                    dy -= reach * (.55 + .72 * wave(1.15, delay + offset));
                    dx += (i === 0 || i === 5 || i === 6 ? -1 : 1) * reach * .48 * wave(1.15, delay + offset + .5);
                }
                if (i === 2 || i === 7) {
                    dy -= reach * .35 * wave(1.15, delay + i);
                }
                break;
            case 'droop':
                dy += reach * .07 * wave(.2, delay + i * .5);
                break;
            case 'recover':
                if ([0, 1, 2, 7].includes(i)) {
                    dy -= reach * (.22 + .43 * wave(.85, delay));
                    dx += (i === 0 || i === 7 ? -1 : 1) * reach * .20 * wave(.85, delay + .5);
                }
                break;
            case 'idle':
                // Gentle micro-sway only, with no expressive choreography.
                break;
        }
        return [x + dx, y + dy];
    }));
    if (name === 'listen')
        headBob = .08 * wave(.4);
    if (name === 'ponder')
        headBob = .07 * wave(.32);
    if (name === 'celebrate')
        headBob = -.25 - .38 * wave(1.15);
    if (name === 'droop')
        headBob = .2 + .04 * wave(.2);
    if (name === 'recover')
        headBob = -.12 - .18 * wave(.85);
    const tick = Math.floor(time * 12);
    let expression = base.face;
    if (tick % 79 === 42 || tick % 79 === 43)
        expression = 'blink';
    else if (name === 'celebrate' && wave(1.15) > .85)
        expression = 'surprised';
    return { ...base, head: [base.head[0], base.head[1] + headBob], limbs: moving, face: expression };
}
/** Smooth, clamped, pure transition of all 48 persistent segment identities. */
export function sampleTransition(from, to, progress) {
    const t = Number.isFinite(progress) ? Math.max(0, Math.min(1, progress)) : 0;
    return interpolate(from, to, t * t * (3 - 2 * t));
}
/** Keep the established eight-unit pose grid; only the rendered head is 30% smaller. */
export const SKIFF_HEAD_SCALE = 0.7;
const HEAD_UNITS = 8;
const HEAD_INSET = HEAD_UNITS * (1 - SKIFF_HEAD_SCALE) / 2;
const fmt = (n) => Number(n.toFixed(3)).toString();
const esc = (s) => s.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;');
const rect = (x, y, w, h, fill, stroke, sw = 0) => `<rect x="${fmt(x)}" y="${fmt(y)}" width="${fmt(w)}" height="${fmt(h)}" fill="${esc(fill)}"${stroke ? ` stroke="${esc(stroke)}" stroke-width="${fmt(sw)}"` : ''}/>`;
/** A pure SVG renderer; its output depends only on Frame. No DOM or image assets required. */
export function renderSvg(frame) {
    validatePose(frame.pose);
    const colors = palettes[frame.palette];
    if (!colors)
        throw new Error('Unknown Skiff palette');
    const [hx, hy] = frame.pose.head;
    const output = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-9 -7 30 29" role="img" aria-label="Skiff pixel octopus">'];
    frame.pose.limbs.forEach((limb, li) => {
        output.push(`<g id="skiff-limb-${li}">`);
        limb.forEach(([x, y], si) => {
            let color = si < 2 ? colors.dark : si < 4 ? colors.mid : si === 4 ? colors.light : colors.tip;
            if (frame.pulse !== 'none' && Math.floor(frame.phase * 12) % 6 === (frame.pulse === 'inward' ? 5 - si : si))
                color = colors.tip;
            // Re-anchor the proximal squares to the smaller head while preserving
            // the six segment identities and every distal tip position.
            const weight = (1 - SKIFF_HEAD_SCALE) * (1 - si / 5);
            const sx = x + (hx + HEAD_UNITS / 2 - (x + .5)) * weight;
            const sy = y + (hy + HEAD_UNITS / 2 - (y + .5)) * weight;
            output.push(`<g id="skiff-limb-${li}-segment-${si}">${rect(sx, sy, 1, 1, color, colors.outline, .09)}</g>`);
        });
        output.push('</g>');
    });
    // Scale the head and all face features together, around the original centre.
    // Tentacle squares remain 1 x 1 logical units and never rotate.
    const px = (x) => hx + HEAD_INSET + x * SKIFF_HEAD_SCALE;
    const py = (y) => hy + HEAD_INSET + y * SKIFF_HEAD_SCALE;
    const dim = (size) => size * SKIFF_HEAD_SCALE;
    output.push('<g id="skiff-head">', rect(px(0), py(0), dim(8), dim(8), colors.body, colors.outline, dim(.15)));
    const eye = (x) => {
        const y = 2.2;
        if (frame.pose.face === 'blink' || frame.pose.face === 'sleeping' || frame.pose.face === 'happy')
            return rect(px(x), py(y + .9), dim(1.5), dim(.28), colors.eye);
        const focused = frame.pose.face === 'focused';
        const surprised = frame.pose.face === 'surprised';
        const height = focused ? 1.05 : surprised ? 1.9 : frame.pose.face === 'concerned' ? 1.35 : 1.65;
        const offset = focused ? .4 : surprised ? -.18 : 0;
        const width = surprised ? 1.7 : 1.55;
        return rect(px(x), py(y + offset), dim(width), dim(height), colors.eye)
            + rect(px(x + .25), py(y + offset + .2), dim(.42), dim(.42), '#f8ffff')
            + rect(px(x + 1.02), py(y + offset + height - .47), dim(.25), dim(.25), colors.light);
    };
    output.push(`<g id="skiff-eye-left">${eye(1.35)}</g>`, `<g id="skiff-eye-right">${eye(5.1)}</g>`);
    // Every expression is one continuous orthogonal pixel glyph.
    const mouth = () => {
        let d;
        switch (frame.pose.face) {
            case 'sleeping':
                d = 'M3.4 5.65 H4.5 V5.92 H3.4 Z';
                break;
            case 'focused':
                d = 'M3.24 5.66 H4.66 V5.91 H3.24 Z';
                break;
            case 'concerned':
                d = 'M3.08 5.90 H3.38 V5.66 H4.5 V5.90 H4.8 V5.42 H4.48 V5.36 H3.4 V5.42 H3.08 Z';
                break;
            case 'surprised':
                d = 'M3.6 5.36 H4.28 V6.04 H3.6 Z M3.83 5.58 V5.82 H4.06 V5.58 Z';
                break;
            default:
                d = 'M3.07 5.44 H3.4 V5.8 H4.5 V5.44 H4.83 V6.05 H3.07 Z';
                break;
        }
        const transformed = d.replace(/([MHV])(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?/g, (_m, cmd, a, b) => {
            if (cmd === 'H')
                return cmd + fmt(px(Number(a)));
            if (cmd === 'V')
                return cmd + fmt(py(Number(a)));
            return cmd + fmt(px(Number(a))) + ' ' + fmt(py(Number(b)));
        });
        return `<path d="${transformed}" fill="${esc(colors.eye)}"${frame.pose.face === 'surprised' ? ' fill-rule="evenodd"' : ''}/>`;
    };
    output.push(`<g id="skiff-mouth">${mouth()}</g>`, '</g>');
    // The thinking tip and its two adjacent squares sit in front of the face.
    // SVG reuse preserves exactly 48 unique segment rectangles.
    if (frame.pose.foregroundTipLimb !== undefined) {
        output.push('<g id="skiff-foreground-tip">');
        for (let segment = 3; segment <= 5; segment++) {
            output.push(`<use href="#skiff-limb-${frame.pose.foregroundTipLimb}-segment-${segment}"/>`);
        }
        output.push('</g>');
    }
    output.push('</svg>');
    return output.join('');
}
const statePresets = {
    idle: { pose: 'idle', face: 'open', pulse: 'none' },
    ready: { pose: 'greet', face: 'happy', pulse: 'outward' },
    receiving: { pose: 'listen', face: 'focused', pulse: 'inward' },
    thinking: { pose: 'ponder', face: 'focused', pulse: 'none' },
    working: { pose: 'ponder', face: 'focused', pulse: 'inward' },
    'output-ready': { pose: 'present', face: 'happy', pulse: 'outward' },
    waiting: { pose: 'listen', face: 'open', pulse: 'none' },
    'connection-interrupted': { pose: 'droop', face: 'concerned', pulse: 'none' },
    recovering: { pose: 'recover', face: 'focused', pulse: 'outward' },
    warning: { pose: 'listen', face: 'concerned', pulse: 'none' },
    error: { pose: 'idle', face: 'concerned', pulse: 'none' },
    sleeping: { pose: 'idle', face: 'sleeping', pulse: 'none' }
};
const moodFaces = {
    neutral: 'open', curious: 'open', pleased: 'happy', excited: 'surprised',
    focused: 'focused', cautious: 'focused', concerned: 'concerned', puzzled: 'focused'
};
/** Critical factual conditions override cosmetic moods and manual faces. */
export function semanticPresentation(state, mood = 'neutral') {
    if (!Object.hasOwn(statePresets, state))
        throw new Error('Unknown Skiff state');
    if (!Object.hasOwn(moodFaces, mood))
        throw new Error('Unknown Skiff mood');
    const result = statePresets[state];
    const critical = ['connection-interrupted', 'warning', 'error', 'sleeping'].includes(state);
    return { ...result, face: critical || mood === 'neutral' ? result.face : moodFaces[mood] };
}
export const skiffSequences = {
    'request-flow': [
        { state: 'receiving', label: 'Receiving a request', durationMs: 1300, transitionMs: 400 },
        { state: 'thinking', label: 'Thinking', durationMs: 1900, transitionMs: 500, mood: 'focused' },
        { state: 'working', label: 'Working', durationMs: 1700, transitionMs: 450 },
        { state: 'output-ready', label: 'Presenting the answer', durationMs: 1450, transitionMs: 500 },
        { state: 'ready', label: 'Ready', durationMs: 900, transitionMs: 350 }
    ],
    'connection-recovery': [
        { state: 'working', label: 'Working normally', durationMs: 1200, transitionMs: 350 },
        { state: 'connection-interrupted', label: 'Connection interrupted', durationMs: 1900, transitionMs: 600 },
        { state: 'recovering', label: 'Restoring the connection', durationMs: 1450, transitionMs: 600 },
        { state: 'ready', label: 'Connection restored', durationMs: 1250, transitionMs: 500 }
    ],
    greeting: [
        { state: 'idle', label: 'Waiting', durationMs: 700, transitionMs: 0 },
        { state: 'ready', label: 'Greeting', durationMs: 2200, transitionMs: 550 },
        { state: 'idle', label: 'Settling down', durationMs: 1100, transitionMs: 550 }
    ]
};
export function sequenceDuration(name) {
    if (!Object.hasOwn(skiffSequences, name))
        throw new Error('Unknown Skiff sequence');
    return skiffSequences[name].reduce((total, step) => total + step.durationMs, 0);
}
const criticalState = (state) => ['connection-interrupted', 'warning', 'error', 'sleeping'].includes(state);
/** Pure deterministic timeline sampling, including reduced-motion stage display. */
export function sampleSequence(name, elapsedMs, motion = true) {
    const steps = skiffSequences[name];
    if (!steps)
        throw new Error('Unknown Skiff sequence');
    const durationMs = sequenceDuration(name);
    const elapsed = Number.isFinite(elapsedMs) ? Math.max(0, Math.min(durationMs, elapsedMs)) : 0;
    let start = 0, index = steps.length - 1;
    for (let i = 0; i < steps.length; i++) {
        if (elapsed < start + steps[i].durationMs) {
            index = i;
            break;
        }
        start += steps[i].durationMs;
    }
    if (elapsed >= durationMs)
        start = durationMs - steps[index].durationMs;
    const step = steps[index];
    const local = Math.min(step.durationMs, elapsed - start);
    const current = semanticPresentation(step.state, step.mood ?? 'neutral');
    let pose = samplePose(current.pose, local / 1000, motion);
    if (index > 0 && motion && step.transitionMs > 0 && local < step.transitionMs) {
        const previous = steps[index - 1];
        const previousPreset = semanticPresentation(previous.state, previous.mood ?? 'neutral');
        const prior = samplePose(previousPreset.pose, previous.durationMs / 1000, motion);
        pose = sampleTransition(prior, pose, local / step.transitionMs);
    }
    // Factual warnings override the interpolated face immediately.
    pose = { ...pose, face: current.face };
    return {
        name, state: step.state, label: step.label, stepIndex: index,
        elapsedMs: elapsed, durationMs, finished: elapsed >= durationMs,
        pose, palette: 'blue', pulse: motion ? current.pulse : 'none', phase: elapsed / 1000
    };
}
export const skiffStates = Object.freeze(Object.keys(statePresets));
export const skiffMoods = Object.freeze(Object.keys(moodFaces));
/** Uses one RAF loop and exposes a semantic boundary for host-welcome. */
let nextSkiffInstanceId = 0;
/** Live SVG IDs are unique per instance; pure renderSvg() baselines remain stable. */
export function createSkiff(container, options = {}) {
    const idScope = `skiff-${++nextSkiffInstanceId}-`;
    const scopedSvg = (frame) => renderSvg(frame)
        .replaceAll('id="skiff-', `id="${idScope}`)
        .replaceAll('href="#skiff-', `href="#${idScope}`);
    let palette = options.palette ?? 'blue';
    let name = 'idle', faceOverride = null, pulse = 'none';
    let state = null, mood = 'neutral';
    let enabled = true, destroyed = false, running = false, handle = 0, origin = null;
    let lastSeconds = 0, poseStart = 0;
    let transition = null;
    let sequence = null;
    const win = container.ownerDocument.defaultView;
    const reduced = options.reducedMotion === undefined || options.reducedMotion === 'auto'
        ? Boolean(win?.matchMedia?.('(prefers-reduced-motion: reduce)').matches)
        : options.reducedMotion;
    const hasMotion = () => !reduced && enabled;
    const poseAt = (time) => {
        const target = samplePose(name, time - poseStart, hasMotion());
        if (!transition)
            return target;
        const progress = (time - transition.start) / transition.duration;
        if (progress >= 1) {
            transition = null;
            return target;
        }
        return sampleTransition(transition.from, target, progress);
    };
    const playbackAt = (time) => {
        if (!sequence)
            return null;
        const target = sequence.pausedAt ?? time;
        return sampleSequence(sequence.name, (target - sequence.started - sequence.pauseTotal) * 1000, hasMotion());
    };
    const draw = (time = lastSeconds) => {
        if (destroyed)
            return;
        lastSeconds = Number.isFinite(time) ? Math.max(0, time) : 0;
        const scene = playbackAt(lastSeconds);
        if (scene) {
            container.innerHTML = scopedSvg({ ...scene, palette });
            return;
        }
        const pose = poseAt(lastSeconds);
        const presentation = state === null ? null : semanticPresentation(state, mood);
        const critical = state !== null && criticalState(state);
        const shownFace = critical ? presentation.face : faceOverride ?? (pose.face === 'blink' ? 'blink' : presentation?.face ?? pose.face);
        const visual = { ...pose, face: shownFace };
        container.innerHTML = scopedSvg({ pose: visual, palette, pulse: hasMotion() ? pulse : 'none', phase: lastSeconds });
    };
    const loop = (now) => {
        if (!running || destroyed)
            return;
        if (origin === null)
            origin = now - lastSeconds * 1000;
        draw((now - origin) / 1000);
        handle = win?.requestAnimationFrame(loop) ?? 0;
    };
    const start = () => { if (!destroyed && !running && hasMotion() && win) {
        running = true;
        handle = win.requestAnimationFrame(loop);
    } };
    const stop = () => { running = false; if (win && handle)
        win.cancelAnimationFrame(handle); handle = 0; };
    const changePose = (next, settings = {}) => {
        if (!Object.hasOwn(poses, next))
            throw new Error('Unknown Skiff pose');
        const ms = settings.duration ?? 420;
        if (!Number.isFinite(ms) || ms < 0)
            throw new RangeError('Transition duration must be finite and nonnegative');
        const from = poseAt(lastSeconds);
        name = next;
        poseStart = lastSeconds;
        transition = hasMotion() && ms > 0 ? { from, start: lastSeconds, duration: ms / 1000 } : null;
        draw();
    };
    const transitionTo = (next, settings = {}) => {
        // Switching to a manual pose intentionally exits semantic state control.
        const leavingState = state !== null;
        state = null;
        sequence = null;
        if (leavingState)
            pulse = 'none';
        changePose(next, settings);
    };
    draw();
    start();
    return {
        setPose(next) { transitionTo(next); },
        transitionTo,
        replay() {
            if (sequence) {
                sequence = { name: sequence.name, started: lastSeconds, pausedAt: null, pauseTotal: 0 };
                draw();
                return;
            }
            const from = poses.idle;
            poseStart = lastSeconds;
            transition = hasMotion() ? { from, start: lastSeconds, duration: .42 } : null;
            draw();
        },
        setState(next) {
            const preset = semanticPresentation(next, mood); // validate before changing state
            sequence = null;
            state = next;
            faceOverride = null;
            pulse = preset.pulse;
            changePose(preset.pose);
        },
        getState() { return state; },
        play(next) {
            sequenceDuration(next);
            sequence = { name: next, started: lastSeconds, pausedAt: null, pauseTotal: 0 };
            transition = null;
            state = null;
            faceOverride = null;
            draw();
            start();
        },
        pause() { if (sequence && sequence.pausedAt === null) {
            sequence.pausedAt = lastSeconds;
            draw();
        } },
        resume() {
            if (sequence && sequence.pausedAt !== null) {
                sequence.pauseTotal += lastSeconds - sequence.pausedAt;
                sequence.pausedAt = null;
                draw();
                start();
            }
        },
        seekSequence(elapsedMs) {
            if (!sequence)
                throw new Error('No active sequence');
            if (!Number.isFinite(elapsedMs))
                throw new RangeError('Invalid sequence time');
            const clamped = Math.max(0, Math.min(sequenceDuration(sequence.name), elapsedMs));
            const anchor = sequence.pausedAt ?? lastSeconds;
            sequence.started = anchor - sequence.pauseTotal - clamped / 1000;
            draw();
        },
        stopSequence() { sequence = null; state = null; pulse = 'none'; changePose('idle'); },
        getPlayback() {
            const frame = playbackAt(lastSeconds);
            return frame ? { name: frame.name, state: frame.state, label: frame.label,
                stepIndex: frame.stepIndex, elapsedMs: frame.elapsedMs,
                durationMs: frame.durationMs, finished: frame.finished,
                paused: sequence?.pausedAt !== null } : null;
        },
        setMood(next) {
            if (!Object.hasOwn(moodFaces, next))
                throw new Error('Unknown Skiff mood');
            mood = next;
            draw();
        },
        setExpression(next) {
            if (next !== null && !['open', 'happy', 'blink', 'focused', 'concerned', 'sleeping', 'surprised'].includes(next))
                throw new Error('Unknown Skiff face');
            faceOverride = next;
            draw();
        },
        setColor(next) { if (!Object.hasOwn(palettes, next))
            throw new Error('Unknown palette'); palette = next; draw(); },
        pulse(next) { if (!['none', 'inward', 'outward'].includes(next))
            throw new Error('Unknown pulse'); pulse = next; draw(); },
        setMotionEnabled(value) {
            enabled = Boolean(value);
            if (!hasMotion()) {
                stop();
                transition = null;
                draw();
            }
            else {
                draw();
                start();
            }
        },
        renderAt(seconds) { draw(seconds); },
        destroy() { destroyed = true; stop(); container.innerHTML = ''; }
    };
}

/** Narrow semantic integration boundary for host-welcome and other Zog interfaces.
 * The application remains authoritative for factual status and accessibility. */

/** No low-level SVG/limb controls escape this application-facing API. */
export function createSkiffPresenter(container, options = {}) {
    const win = container.ownerDocument.defaultView;
    const reduced = options.reducedMotion === true ||
        (options.reducedMotion !== false && !!win?.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
    const engine = createSkiff(container, options);
    let destroyed = false;
    let task = null;
    let watcher = 0;
    const listeners = new Set();
    const ensureLive = () => { if (destroyed)
        throw new Error('Skiff presenter is destroyed'); };
    const notify = (event) => {
        for (const listener of [...listeners]) {
            try {
                listener(event);
            }
            catch { /* Consumer callbacks cannot break the renderer or settlement. */ }
        }
    };
    const clearWatcher = () => { if (watcher && win)
        win.cancelAnimationFrame(watcher); watcher = 0; };
    const cancel = (reason) => {
        if (!task)
            return;
        const previous = task;
        task = null;
        clearWatcher();
        const result = { name: previous.name, status: 'cancelled', reason };
        previous.resolve(result);
        notify({ type: 'sequence-cancelled', name: previous.name, reason });
    };
    const complete = () => {
        if (!task)
            return;
        const previous = task;
        task = null;
        clearWatcher();
        previous.resolve({ name: previous.name, status: 'completed' });
        notify({ type: 'sequence-completed', name: previous.name });
    };
    const observe = () => {
        watcher = 0;
        if (destroyed || !task)
            return;
        if (engine.getPlayback()?.finished) {
            complete();
            return;
        }
        watcher = win?.requestAnimationFrame(observe) ?? 0;
    };
    return {
        setState(next) {
            ensureLive();
            semanticPresentation(next); // validate before interrupting a valid sequence
            cancel('state-change');
            engine.setState(next);
            notify({ type: 'state-changed', state: next });
        },
        setMood(next) { ensureLive(); engine.setMood(next); },
        getState() { ensureLive(); return engine.getPlayback()?.state ?? engine.getState(); },
        playSequence(name) {
            ensureLive();
            sequenceDuration(name); // fail closed on unknown choreography
            cancel('superseded');
            if (reduced || !win?.requestAnimationFrame) {
                // No ongoing loop or hanging completion promise in reduced-motion mode.
                // Display the final, factual state as a still frame.
                const finalState = skiffSequences[name].at(-1).state;
                engine.setState(finalState);
                notify({ type: 'state-changed', state: finalState });
                notify({ type: 'sequence-completed', name });
                return Promise.resolve({ name, status: 'completed' });
            }
            engine.play(name);
            return new Promise(resolve => {
                task = { name, resolve };
                watcher = win.requestAnimationFrame(observe);
            });
        },
        stop() { ensureLive(); cancel('stopped'); engine.stopSequence(); },
        subscribe(callback) {
            ensureLive();
            listeners.add(callback);
            return () => { listeners.delete(callback); };
        },
        destroy() {
            if (destroyed)
                return;
            cancel('destroyed');
            destroyed = true;
            clearWatcher();
            engine.destroy();
            listeners.clear();
        }
    };
}
