// nsq-media: a separate, PUBLIC worker that serves finished post images so Instagram can fetch them.
// The dashboard worker stays fully behind Cloudflare Access.
// Secret: GITHUB_TOKEN (fine-grained, Contents: read-only, this repo only).
const REPO = 'oschmidek-collab/no-stupid-questions';

export default {
  async fetch(request, env) {
    const m = new URL(request.url).pathname.match(/^\/media\/([a-z0-9_-]+)\/(\d{2})\.jpg$/);
    if (!m || (request.method !== 'GET' && request.method !== 'HEAD')) return new Response('Not found', { status: 404 });
    const r = await fetch(`https://api.github.com/repos/${REPO}/contents/media/${m[1]}/${m[2]}.jpg`, {
      headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: 'application/vnd.github.raw+json', 'User-Agent': 'nsq-media' },
    });
    if (!r.ok) return new Response('Not found', { status: 404 });
    return new Response(request.method === 'HEAD' ? null : r.body, {
      headers: { 'Content-Type': 'image/jpeg', 'Cache-Control': 'public, max-age=3600' },
    });
  },
};
