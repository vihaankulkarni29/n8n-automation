// n8n Function node snippet: Normalize raw source payloads to a common schema

// Input: items[] with fields including sourceType, url/source_url and source-specific fields
// Output: items[] each with normalized fields

function normalize(item) {
  const src = (item.sourceType || item.source_type || '').toLowerCase();
  const out = {
    source: src || 'generic',
    source_url: item.url || item.source_url || '',
    name: '',
    industry_category: '',
    description: '',
    website: item.website || '',
    website_present: !!(item.website),
    socials: item.socials || {},
    contact_info: item.contact_info || {},
    metrics: item.metrics || {},
    assets: item.assets || {},
  };

  switch (src) {
    case 'yc':
      out.name = item.name || '';
      out.industry_category = item.industry || item.category || 'Unspecified';
      out.description = item.description || '';
      out.website = item.website || '';
      out.website_present = !!out.website;
      break;
    case 'modemonline':
      out.name = item.name || '';
      out.industry_category = item.category || 'Fashion/Apparel';
      out.description = item.description || '';
      out.website = item.website || '';
      out.website_present = !!out.website;
      out.contact_info = { email: item.email || '', phone: item.phone || '' };
      break;
    case 'justdial':
    case 'zomato':
      out.name = item.name || '';
      out.industry_category = item.cuisines || 'Restaurants';
      out.description = item.listing_description || '';
      out.website = item.website || '';
      out.website_present = !!out.website;
      out.contact_info = { phone: item.phone || '', email: item.email || '' };
      out.metrics = {
        reviews: item.reviews || 0,
        rating: item.rating || null,
        price_level: item.price_level || null,
      };
      break;
    case 'instagram_hashtag':
    case 'linkedin_hashtag':
      out.name = item.account_name || item.handle || '';
      out.industry_category = item.industry || 'Unspecified';
      out.description = item.bio || item.tagline || '';
      out.website = item.profile_website || '';
      out.website_present = !!out.website;
      out.socials = Object.assign({}, out.socials, {
        profile: item.profile_url || '',
      });
      out.metrics = Object.assign({}, out.metrics, {
        followers: item.followers || 0,
      });
      break;
    case 'reddit':
    case 'twitter':
      out.name = item.account_name || item.author || '';
      out.industry_category = item.industry || 'Unspecified';
      out.description = item.bio || item.thread_excerpt || item.caption || '';
      out.website = item.website || '';
      out.website_present = !!out.website;
      out.socials = Object.assign({}, out.socials, {
        profile: item.profile_url || '',
      });
      out.metrics = Object.assign({}, out.metrics, {
        followers: item.followers || 0,
        upvotes: item.upvotes || 0,
      });
      break;
    default:
      out.name = item.name || '';
      out.industry_category = item.industry || item.category || 'Unspecified';
      out.description = item.description || item.summary || '';
      break;
  }

  // Ensure socials/contact objects
  out.socials = out.socials || {};
  out.contact_info = out.contact_info || {};
  return out;
}

return items.map(i => ({ json: normalize(i.json || i) }));
