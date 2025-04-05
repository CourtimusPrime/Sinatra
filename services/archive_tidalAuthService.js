// services/tidalAuthService.js
console.log("🎯 services/tidalAuthService.js loaded!");

/**
 * 🌐 Platform: TIDAL
 * 🔒 OAuth: PKCE + Session state required
 * 📥 Needs Request Context: Yes
 * 📤 Scopes: r_usr, w_usr, w_sub, offline_access
 */

const axios = require('axios');
const crypto = require('crypto');
require('dotenv').config(); // Must be at the top
const { updateUserToken } = require('./tidalService');

const CLIENT_ID = process.env.TIDAL_CLIENT_ID;
const CLIENT_SECRET = process.env.TIDAL_CLIENT_SECRET;
const REDIRECT_URI = process.env.TIDAL_REDIRECT_URI;

const AUTH_URL = 'https://login.tidal.com/authorize';
const TOKEN_URL = 'https://auth.tidal.com/v1/oauth2/token';

if (!CLIENT_ID || !CLIENT_SECRET || !REDIRECT_URI) {
  console.error("❌ Missing TIDAL env variables:");
  console.log({ CLIENT_ID, CLIENT_SECRET, REDIRECT_URI });
  throw new Error("TIDAL auth config is incomplete");
}

// 🧬 Generate PKCE codes
function base64URLEncode(buffer) {
  return buffer
    .toString('base64')
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

// 🔐 Build the TIDAL OAuth URL
function buildAuthURL(req) {
  console.log("🧪 typeof generatePKCECodes:", typeof generatePKCECodes);
  const { codeVerifier, codeChallenge } = generatePKCECodes();
  req.session.codeVerifier = codeVerifier;

  console.log("📡 Using TIDAL_CLIENT_ID:", CLIENT_ID);

  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    response_type: 'code',
    redirect_uri: REDIRECT_URI,
    scope: 'r_usr w_usr w_sub offline_access',
    code_challenge: codeChallenge,
    code_challenge_method: 'S256'
  });

  return `${AUTH_URL}?${params.toString()}`;
}

// 🔁 Handle TIDAL callback and exchange token
async function handleTidalCallback(req, code) {
  const codeVerifier = req.session.codeVerifier;
  if (!codeVerifier) throw new Error('Missing code_verifier in session');

  const payload = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    client_id: CLIENT_ID,
    client_secret: CLIENT_SECRET,
    redirect_uri: REDIRECT_URI,
    code_verifier: codeVerifier
  });

  const response = await axios.post(TOKEN_URL, payload, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });

  const { access_token, refresh_token, expires_in } = response.data;

  const userProfile = await axios.get('https://api.tidal.com/v1/me', {
    headers: {
      Authorization: `Bearer ${access_token}`
    }
  });

  const userId = userProfile.data.uuid;

  await updateUserToken(userId, {
    access_token,
    refresh_token,
    expires_in
  });

  return userId;
}

module.exports = {
  buildAuthURL,
  handleTidalCallback
};