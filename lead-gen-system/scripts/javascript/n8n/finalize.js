// n8n Function node snippet: finalize normalized item with timestamp and hash

function djb2(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i);
    hash = hash & hash; // 32-bit
  }
  return (hash >>> 0).toString(16);
}

return items.map(i => {
  const j = i.json || i;
  const now = new Date().toISOString();
  const name = (j.name || '').toLowerCase();
  const site = (j.website || j.source_url || '').toLowerCase();
  const src = (j.source || j.source_type || 'generic').toLowerCase();
  const key = djb2([name, site, src].join('|'));
  return { json: { ...j, timestamp: now, hash_key: key } };
});
