// Cloudflare Pages Function: POST /api/tasks  {id, done}
// Saves a checklist tick by committing data/tasks.json back to the GitHub repo.
// Env vars (Cloudflare → Pages → Settings → Variables): GITHUB_TOKEN (fine-grained, Contents: read/write on this repo only), GITHUB_REPO ("owner/name").
// The site sits behind Cloudflare Access, so only the owner can reach this endpoint.

const PATH = 'data/tasks.json';

export async function onRequestPost({ request, env }) {
  let body;
  try { body = await request.json(); } catch { return json({ error: 'Request body must be JSON' }, 400); }
  const { id, done } = body || {};
  if (typeof id !== 'string' || typeof done !== 'boolean') return json({ error: 'Expected {id: string, done: boolean}' }, 400);

  const api = `https://api.github.com/repos/${env.GITHUB_REPO}/contents/${PATH}`;
  const headers = {
    Authorization: `Bearer ${env.GITHUB_TOKEN}`,
    Accept: 'application/vnd.github+json',
    'User-Agent': 'nsq-dashboard',
  };

  // Retry once if someone else (the engine) committed between our read and write.
  for (let attempt = 0; attempt < 2; attempt++) {
    const cur = await fetch(api, { headers });
    if (!cur.ok) return json({ error: `Could not read tasks (${cur.status})` }, 502);
    const file = await cur.json();
    const tasks = JSON.parse(decodeB64(file.content));
    const task = tasks.find(t => t.id === id);
    if (!task) return json({ error: `No task with id ${id}` }, 404);
    if (task.done === done) return json({ ok: true, unchanged: true });
    task.done = done;
    task.done_at = done ? new Date().toISOString() : null;

    const put = await fetch(api, {
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
  const bytes = new TextEncoder().encode(str);
  let bin = '';
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin);
}
