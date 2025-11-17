// n8n Function node snippet: Quick parse of fetched HTML page
// Expects item.json.body (HTML as string) and item.json.source_type/value
// Produces a lightweight object with guessed name, description, and website

function extractMeta(html, name, attr, value) {
  const regex = new RegExp(`<${name}[^>]*${attr}=["']${value}["'][^>]*>`, 'i');
  const m = html.match(regex);
  if (!m) return null;
  const tag = m[0];
  const contentMatch = tag.match(/content=["']([^"']*)["']/i);
  return contentMatch ? contentMatch[1] : null;
}

function extractTitle(html){
  const m = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  return m ? m[1].trim() : '';
}

function extractCanonical(html){
  const m = html.match(/<link[^>]+rel=["']canonical["'][^>]*href=["']([^"']+)["'][^>]*>/i);
  return m ? m[1] : '';
}

function sanitize(s){
  return (s||'').replace(/[\n\r\t]+/g,' ').trim();
}

return items.map(i => {
  const j = i.json || {};
  const html = String(j.body || j.html || '');
  let name = extractMeta(html, 'meta', 'property', 'og:site_name') || extractTitle(html);
  let desc = extractMeta(html, 'meta', 'name', 'description') || extractMeta(html, 'meta', 'property', 'og:description') || '';
  const canonical = extractCanonical(html);
  name = sanitize(name);
  desc = sanitize(desc);
  const out = {
    sourceType: j.source_type || j.sourceType || 'generic',
    source_url: j.value || j.url || j.source_url || '',
    name,
    description: desc,
    website: canonical || j.value || j.url || '',
    metrics: {},
    assets: {}
  };
  return { json: out };
});
