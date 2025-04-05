// services/auth/tidal.js

const axios = require('axios'); // make sure this is at the top of your file

console.log("👀 services/auth/tidal.js loaded!");

const CLIENT_ID = process.env.TIDAL_CLIENT_ID;
const CLIENT_SECRET = process.env.TIDAL_CLIENT_SECRET;
const REDIRECT_URI = process.env.TIDAL_REDIRECT_URI;
const crypto = require('crypto');

function base64URLEncode(buffer) {
  return buffer.toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

function generatePKCECodes() {
  const codeVerifier = base64URLEncode(crypto.randomBytes(64));
  const codeChallenge = base64URLEncode(
    crypto.createHash('sha256').update(codeVerifier).digest()
  );
  return { codeVerifier, codeChallenge };
}
console.log("🔐 CLIENT_ID:", CLIENT_ID);

function buildAuthURL(req) {
  const { codeVerifier, codeChallenge } = generatePKCECodes();
  req.session.codeVerifier = codeVerifier; // Store code_verifier in session

  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    response_type: 'code',
    redirect_uri: REDIRECT_URI,
    scope: [
      'user.read',
      'collection.read',
      'playlists.read',
      'playlists.write',
      'collection.write',
      'entitlements.read',
      'playback',
      'recommendations.read'
    ].join(' '),
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
    state: 'tidal'
  });

  console.log("🌊 TIDAL Auth URL params:", params.toString());
  return `https://login.tidal.com/authorize?${params.toString()}`;
}

async function handleCallback(req, code) {
  const codeVerifier = req.session.codeVerifier;
  if (!codeVerifier) throw new Error('Missing code_verifier in session');

  const payload = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    code_verifier: codeVerifier
  });

  console.log("📦 Token exchange payload:", payload.toString());

  let access_token, refresh_token, expires_in;

  try {
    const response = await axios.post('https://auth.tidal.com/v1/oauth2/token', payload, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

    ({ access_token, refresh_token, expires_in } = response.data);
    console.log("🔑 TIDAL access_token received!");
  } catch (err) {
    console.error("❌ Token exchange failed:");
    console.error("↳ Status:", err.response?.status);
    console.error("↳ Data:", err.response?.data);
    throw err;
  }

  try {
    // Updated the user profile endpoint to v2
    const userProfile = await axios.get('https://api.tidal.com/v2/me', {
      headers: {
        Authorization: `Bearer ${access_token}`
      }
    });

    const userId = userProfile.data.uuid;
    console.log(`✅ Authenticated TIDAL user: ${userId}`);

    // Optionally: save token here (e.g., store access_token, refresh_token, and expiration)
    return userId;

  } catch (err) {
    console.error("❌ Failed to fetch TIDAL user profile:");
    console.error("↳ Status:", err.response?.status);
    console.error("↳ Data:", err.response?.data);
    throw err;
  }
}
  
module.exports = {
  buildAuthURL,
  handleCallback
};