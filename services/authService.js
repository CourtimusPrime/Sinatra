// services/authService.js
const axios = require('axios');
const querystring = require('querystring');
const { updateUserToken, storeUserPlaylists } = require('./spotifyService'); // 👈 add storeUserPlaylists

const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const REDIRECT_URI = process.env.NODE_ENV === "production"
    ? `${process.env.PROD_URL}/callback`
    : "http://localhost:3000/callback";

const TOKEN_URL = 'https://accounts.spotify.com/api/token';

/**
 * Builds the Spotify authorization URL
 */
function buildAuthURL() {
    const scope = 'user-top-read playlist-read-private playlist-read-collaborative';
    const SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize';
    return `${SPOTIFY_AUTH_URL}?response_type=code&client_id=${CLIENT_ID}&scope=${encodeURIComponent(scope)}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}`;
}

/**
 * Handles Spotify auth callback: exchanges code for token, fetches user, stores in DB, and stores playlists
 */
async function handleSpotifyCallback(code) {
    if (!code) throw new Error("Missing authorization code.");

    // Exchange code for token
    const tokenResponse = await axios.post(
        TOKEN_URL,
        querystring.stringify({
            grant_type: 'authorization_code',
            code,
            redirect_uri: REDIRECT_URI,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET
        }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );

    const { access_token, refresh_token, expires_in } = tokenResponse.data;

    // Fetch the current Spotify user
    const userResponse = await axios.get('https://api.spotify.com/v1/me', {
        headers: { Authorization: `Bearer ${access_token}` }
    });

    const spotifyUser = userResponse.data;
    const userId = spotifyUser.id; // <-- Use this as your unique identifier

    // Store the user's token in MongoDB
    await updateUserToken(userId, {
        access_token,
        refresh_token,
        expires_in
    });

    // Store the user's public playlists
    await storeUserPlaylists(userId, access_token);

    return userId; // Return userId (not display_name)
}

module.exports = {
    buildAuthURL,
    handleSpotifyCallback
};