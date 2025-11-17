// n8n Function node snippet: Detect source type from input text/URL/hashtag

function detect(input) {
  const text = String(input || '').trim();
  if (!text) return { source_type: 'generic', value: '' };
  // Hashtags
  if (text.startsWith('#')) {
    // Caller should decide platform; default to instagram_hashtag
    return { source_type: 'instagram_hashtag', value: text.slice(1) };
  }
  // URLs
  let url = text;
  try { url = new URL(text).href; } catch(e) {}
  const lower = url.toLowerCase();
  if (lower.includes('ycombinator.com/companies')) return { source_type: 'yc', value: url };
  if (lower.includes('modemonline')) return { source_type: 'modemonline', value: url };
  if (lower.includes('justdial.com')) return { source_type: 'justdial', value: url };
  if (lower.includes('zomato.com')) return { source_type: 'zomato', value: url };
  if (lower.includes('instagram.com')) return { source_type: 'instagram', value: url };
  if (lower.includes('linkedin.com')) return { source_type: 'linkedin', value: url };
  if (lower.includes('twitter.com') || lower.includes('x.com')) return { source_type: 'twitter', value: url };
  if (lower.includes('reddit.com')) return { source_type: 'reddit', value: url };
  return { source_type: 'generic', value: url };
}

// Expect input items with a field `query` (email/webhook payload containing a URL or hashtag)
return items.map(i => {
  const q = (i.json && (i.json.query || i.json.text || i.json.url)) || '';
  const res = detect(q);
  return { json: { ...i.json, ...res } };
});
