// n8n Function node snippet: Compute branding score for a normalized item
// Rules (from spec):
// - No website = +3
// - Short/generic description (<150 chars) = +2
// - No social links = +2
// - High reviews/followers but poor branding = +2

function computeScore(n) {
  let score = 0;
  if (!n.website_present) score += 3;
  const desc = (n.description || '').trim();
  if (desc.length > 0 && desc.length < 150) score += 2;
  const hasSocials = n.socials && Object.keys(n.socials).length > 0 && Object.values(n.socials).some(Boolean);
  if (!hasSocials) score += 2;
  const followers = Number(n.metrics?.followers || 0);
  const reviews = Number(n.metrics?.reviews || 0);
  const brandingQuality = n.assets?.branding_quality || 'unknown';
  if ((followers >= 5000 || reviews >= 200) && (brandingQuality === 'poor' || brandingQuality === 'unknown')) {
    score += 2;
  }
  return score;
}

return items.map(i => {
  const n = i.json || i;
  const score = computeScore(n);
  return { json: { ...n, score } };
});
