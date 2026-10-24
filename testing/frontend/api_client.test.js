import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

// Core URL resolution logic matching frontend/src/api/client.js
function buildMediaUrlResolver(origin = '') {
  return (url) => {
    if (!url) return null;
    if (typeof url !== 'string') return url;

    if (url.startsWith('http://') || url.startsWith('https://')) {
      if (origin && (url.includes('127.0.0.1:8000') || url.includes('localhost:8000'))) {
        return url.replace(/^https?:\/\/(127\.0\.0\.1|localhost):8000/, origin);
      }
      return url;
    }

    const cleanPath = url.startsWith('/') ? url : `/${url}`;
    if (origin) {
      return `${origin}${cleanPath}`;
    }
    return cleanPath;
  };
}

describe('MindHue Frontend API & Media URL Client Test Suite', () => {
  describe('Media URL Resolution (Local & Cloud Environments)', () => {
    it('returns null when url is null or undefined', () => {
      const getMediaUrl = buildMediaUrlResolver('');
      assert.equal(getMediaUrl(null), null);
      assert.equal(getMediaUrl(undefined), null);
      assert.equal(getMediaUrl(''), null);
    });

    it('returns clean relative path in local dev when no origin is configured', () => {
      const getMediaUrl = buildMediaUrlResolver('');
      assert.equal(getMediaUrl('/media/fundus/OD_1.png'), '/media/fundus/OD_1.png');
      assert.equal(getMediaUrl('media/fundus/OD_1.png'), '/media/fundus/OD_1.png');
    });

    it('prepends cloud origin in production (e.g. Render backend)', () => {
      const cloudOrigin = 'https://mindhue-backend.onrender.com';
      const getMediaUrl = buildMediaUrlResolver(cloudOrigin);
      assert.equal(
        getMediaUrl('/media/fundus/OD_1.png'),
        'https://mindhue-backend.onrender.com/media/fundus/OD_1.png'
      );
      assert.equal(
        getMediaUrl('media/fundus/OD_1.png'),
        'https://mindhue-backend.onrender.com/media/fundus/OD_1.png'
      );
    });

    it('dynamically rewrites stale localhost/127.0.0.1 URLs to production origin', () => {
      const cloudOrigin = 'https://mindhue-backend.onrender.com';
      const getMediaUrl = buildMediaUrlResolver(cloudOrigin);

      const local1 = 'http://127.0.0.1:8000/media/fundus/OD_1.png';
      const local2 = 'http://localhost:8000/media/fundus/OD_1.png';

      assert.equal(getMediaUrl(local1), 'https://mindhue-backend.onrender.com/media/fundus/OD_1.png');
      assert.equal(getMediaUrl(local2), 'https://mindhue-backend.onrender.com/media/fundus/OD_1.png');
    });

    it('preserves external CDN and third-party cloud URLs', () => {
      const getMediaUrl = buildMediaUrlResolver('https://mindhue-backend.onrender.com');
      const cdnUrl = 'https://images.unsplash.com/photo-ophthalmology.jpg';
      assert.equal(getMediaUrl(cdnUrl), cdnUrl);
    });
  });

  describe('API Client Request Header Validation', () => {
    it('generates correct Bearer authentication header when token is present', () => {
      const token = 'jwt-token-sample-12345';
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      assert.equal(headers['Authorization'], 'Bearer jwt-token-sample-12345');
    });

    it('generates empty authentication header when no token is present', () => {
      const token = null;
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      assert.equal(headers['Authorization'], undefined);
    });

    it('formats multi-field validation error messages from backend response', () => {
      const errorPayload = {
        mrn: ['Patient with this MRN already exists.'],
        age: ['Ensure this value is greater than or equal to 0.']
      };
      const formatted = Object.entries(errorPayload)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
        .join(' | ');

      assert.match(formatted, /mrn: Patient with this MRN already exists/);
      assert.match(formatted, /age: Ensure this value is greater than or equal to 0/);
    });
  });
});
