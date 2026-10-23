// Cloudflare Worker for the dashboard ("מחברת המעבדה").
// - Static files come from ./site (assets binding).
// - GET  /data/<name>.json → read live from the GitHub repo, so the dashboard always shows the latest state
//   without a redeploy every time the engine commits.
// - POST /api/tasks {id, done} → tick/untick a checklist task by committing data/tasks.json.
//
// Config: GITHUB_REPO is set in wrangler.jsonc. GITHUB_TOKEN is a secret set in the Cloudflare dashboard
// (fine-grained token, Contents: read/write, this repo only). The site is protected by Cloudflare Access.

const DATA_FILES = new Set(['tasks', 'queue', 'questions', 'metrics', 'decisions']);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    const m = url.pathname.match(/^\/data\/([a-z]+)\.json$/);
    if (m && request.method === 'GET') return getData(m[1], env);

    if (url.pathname === '/api/tasks') {
      if (request.method !== 'POST') return json({ error: 'Use POST' }, 405);
      return saveTask(request, env);
    }

    return env.ASSETS.fetch(request);
  },
};

function gh(env, path) {
  return {
    url: `https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'nsq-dashboard',
    },
  };
}

async function getData(name, env) {
  if (!DATA_FILES.has(name)) return json({ error: 'Unknown data file' }, 404);
  if (!env.GITHUB_TOKEN) return json({ error: 'GITHUB_TOKEN is not set in the Worker settings' }, 500);
  const { url, headers } = gh(env, `data/${name}.json`);
  const r = await fetch(url, { headers: { ...headers, Accept: 'application/vnd.github.raw+json' } });
  if (!r.ok) return json({ error: `Could not read ${name} from GitHub (${r.status})` }, 502);
  return new Response(await r.text(), {
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  });
}

async function saveTask(request, env) {
  let body;
  try { body = await request.json(); } catch { return json({ error: 'Request body must be JSON' }, 400); }
  const { id, done } = body || {};
  if (typeof id !== 'string' || typeof done !== 'boolean') return json({ error: 'Expected {id: string, done: boolean}' }, 400);
  if (!env.GITHUB_TOKEN) return json({ error: 'GITHUB_TOKEN is not set in the Worker settings' }, 500);

  const { url, headers } = gh(env, 'data/tasks.json');
  // Retry once if the engine committed between our read and our write.
  for (let attempt = 0; attempt < 2; attempt++) {
    const cur = await fetch(url, { headers });
    if (!cur.ok) return json({ error: `Could not read tasks (${cur.status})` }, 502);
    const file = await cur.json();
    const tasks = JSON.parse(decodeB64(file.content));
    const task = tasks.find(t => t.id === id);
    if (!task) return json({ error: `No task with id ${id}` }, 404);
    if (task.done === done) return json({ ok: true, unchanged: true });
    task.done = done;
    task.done_at = done ? new Date().toISOString() : null;

    const put = await fetch(url, {
      method: 'PUT',
      headers,
      body: JSON.stringify({
        message: `checklist: ${done ? 'done' : 'undo'} ${id}`,
        content: encodeB64(JSON.stringify(tasks, null, 1)),
        sha: file.sha,
      }),
    });
    if (put.ok) return json({ ok: true });
    if (put.status !== 409) return json({ error: `Could not save (${put.status})` }, 502);
  }
  return json({ error: 'The file kept changing. Try again in a moment.' }, 409);
}

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json' } });

// UTF-8 safe base64 (Hebrew text)
function decodeB64(b64) {
  const bin = atob(b64.replace(/\n/g, ''));
  return new TextDecoder().decode(Uint8Array.from(bin, c => c.charCodeAt(0)));
}
function encodeB64(str) {
  let bin = '';
  for (const b of new TextEncoder().encode(str)) bin += String.fromCharCode(b);
  return btoa(bin);
}
