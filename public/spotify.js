require('dotenv').config();
const express = require('express');
const axios = require('axios');
const querystring = require('querystring');
const cors = require('cors');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, 'public')));

const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const REDIRECT_URI = 'http://localhost:3000/callback';

const SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize';
const TOKEN_URL = 'https://accounts.spotify.com/api/token';

app.get('/login', (req, res) => {
    const scope = 'user-top-read';
    const authURL = `${SPOTIFY_AUTH_URL}?${querystring.stringify({
        response_type: 'code',
        client_id: CLIENT_ID,
        scope,
        redirect_uri: REDIRECT_URI
    })}`;
    res.redirect(authURL);
});

app.get('/callback', async (req, res) => {
    const { code } = req.query;
    try {
        const response = await axios.post(
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

        res.redirect(`/index.html?access_token=${response.data.access_token}`);
    } catch (error) {
        res.send('Error fetching access token.');
    }
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(3000, () => {
    console.log('Server running on http://localhost:3000');
});

async function getTopTracks(token) {
    const response = await fetch('https://api.spotify.com/v1/me/top/tracks?time_range=long_term&limit=10', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    return (await response.json()).items;
}

async function displayTracks() {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('access_token');

    if (!accessToken) {
        document.body.innerHTML = `<a href="http://localhost:3000/login">Login with Spotify</a>`;
        return;
    }

    const topTracks = await getTopTracks(accessToken);
    const trackList = topTracks.map(({ name, artists, album }) =>
        `<li>
            <img src="${album.images[0].url}" alt="${name} album cover" width="50">
            ${name} by ${artists.map(a => a.name).join(', ')}
        </li>`
    ).join('');

    document.getElementById('track-list').innerHTML = trackList;
}

window.onload = displayTracks;