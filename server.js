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

let userStore = [
    {name: "amborn02", token: "", refresh_token: "", expire_moment: ""}
]

function updateUserToken(username, tokenResponse) {
    let current_record = userStore.find((op) => op.name = username)

    if (current_record) {
        current_record.token = tokenResponse.access_token
        current_record.refresh_token = tokenResponse.refresh_token
        current_record.expire_moment = new Date().getTime() + tokenResponse.expires_in * 1000
    }
    else {
        userStore.push({
            name: username,
            token: tokenResponse.access_token,
            refresh_token: tokenResponse.refresh_token,
            expire_moment: new Date().getTime() + tokenResponse.expires_in * 1000
        })
    }
}

async function requestWithUser(user, endpoint) {
    let current_record = userStore.find((op) => op.name = user)
    if (current_record) {
        const response = await axios.get(endpoint, {
            headers: { 'Authorization': `Bearer ${current_record.token}` }
        });
        return response.data;
    }
}

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

        const user = await axios.get('https://api.spotify.com/v1/me', {
            headers: { 'Authorization': `Bearer ${response.data.access_token}` }
        });

        updateUserToken(user.data.display_name, response.data)

        res.redirect(`/${user.data.display_name}`);
    } catch (error) {
        res.send('Error fetching access token.');
    }
});

app.get('/user', async (req, res) => {
    const userData = await requestWithUser(req.query.username, 'https://api.spotify.com/v1/me')
    if (userData) {
        res.send(userData)
    }
    else {
        res.send("Invalid User")
    }
})

app.get('/toptracks', async (req, res) => {
    const tracks = await requestWithUser(req.query.username, 'https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=5')
    if (tracks) {
        res.send(tracks.items)
    }
    else {
        res.send("Invalid User")
    }
})

app.get('/*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(3000, () => {
    console.log('Server running on http://localhost:3000');
});