import { Auth } from '@auth/core';
import { authConfig } from '../../lib/auth-config.js';

export default async function handler(req, res) {
  try {
    const request = toWebRequest(req);
    const response = await Auth(request, authConfig);
    await sendWebResponse(response, res);
  } catch (error) {
    console.error('[auth] Error:', error);
    res.status(500).json({ error: 'Internal auth error' });
  }
}

function toWebRequest(req) {
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  const proto = req.headers['x-forwarded-proto'] || 'https';
  const url = new URL(req.url, `${proto}://${host}`);

  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (value) {
      headers.set(key, Array.isArray(value) ? value.join(', ') : String(value));
    }
  }

  const init = { method: req.method, headers };

  if (req.method !== 'GET' && req.method !== 'HEAD' && req.body) {
    const ct = req.headers['content-type'] || '';
    if (ct.includes('application/x-www-form-urlencoded')) {
      init.body = new URLSearchParams(req.body).toString();
    } else {
      init.body =
        typeof req.body === 'string' ? req.body : JSON.stringify(req.body);
    }
  }

  return new Request(url, init);
}

async function sendWebResponse(webResponse, nodeRes) {
  nodeRes.status(webResponse.status);

  for (const [key, value] of webResponse.headers.entries()) {
    if (key.toLowerCase() === 'set-cookie') {
      const cookies = webResponse.headers.getSetCookie
        ? webResponse.headers.getSetCookie()
        : value.split(', ');
      cookies.forEach((c) => nodeRes.appendHeader('Set-Cookie', c));
    } else {
      nodeRes.setHeader(key, value);
    }
  }

  const body = await webResponse.text();
  nodeRes.send(body);
}
