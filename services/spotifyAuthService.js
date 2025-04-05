// services/spotifyAuthService.js

/**
 * 🌐 Platform: Spotify
 * 🔒 OAuth: Basic Auth (no PKCE)
 * 📥 Needs Request Context: No
 * 📤 Scopes: user-top-read, playlist-read-private, playlist-read-collaborative
 */

const axios = require('axios');
const querystring = require('querystring');
const { updateUserToken, storeUserPlaylists } = require('./spotifyService');

const CLIENT_ID = process.env.SPOTIFY_ID;
const CLIENT_SECRET = process.env.SPOTIFY_SECRET;
const REDIRECT_URI = process.env.NODE_ENV === "production"
    ? `${process.env.PROD_URL}/callback`
    : "http://localhost:3000/callback";

const TOKEN_URL = 'https://accounts.spotify.com/api/token';

function buildAuthURL() {
    const scope = 'user-top-read playlist-read-private playlist-read-collaborative';
    const SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize';
    return `${SPOTIFY_AUTH_URL}?response_type=code&client_id=${CLIENT_ID}&scope=${encodeURIComponent(scope)}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}`;
}

async function handleSpotifyCallback(code) {
    if (!code) throw new Error("Missing authorization code.");
  
    const tokenResponse = await axios.post(
      TOKEN_URL,
      querystring.stringify({
        grant_type: 'authorization_code',
        code,
        redirect_uri: REDIRECT_URI,
        client_id: CLIENT_ID,
        client_secret: CLIENT_SECRET,
      }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
  
    const { access_token, refresh_token, expires_in } = tokenResponse.data;
  
    const userResponse = await axios.get('https://api.spotify.com/v1/me', {
      headers: { Authorization: `Bearer ${access_token}` }
    });
  
    const spotifyUser = userResponse.data;
    const userId = spotifyUser.id;
  
    await updateUserToken(userId, { access_token, refresh_token, expires_in });
    await storeUserPlaylists(userId, access_token);
  
    return userId;
  }

module.exports = {
    buildAuthURL,
    handleSpotifyCallback
};