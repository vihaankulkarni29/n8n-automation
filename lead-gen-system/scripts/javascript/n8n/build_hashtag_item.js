// n8n Function node snippet: Build minimal item for hashtag inputs
// Expects: item.json.source_type in {instagram_hashtag, linkedin_hashtag} and item.json.value (hashtag text without #)
// Produces: basic object consumable by normalize.js

return items.map(i => {
  const j = i.json || {};
  const tag = j.value || j.hashtag || '';
  const platform = j.source_type || 'instagram_hashtag';
  const out = {
    sourceType: platform,
    source_url: `#${tag}`,
    account_name: '',
    bio: '',
    profile_website: '',
    profile_url: '',
    followers: 0,
    industry: 'Unspecified'
  };
  return { json: out };
});
