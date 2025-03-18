require('dotenv').config();
const express = require('express');
const axios = require('axios');
const querystring = require('querystring');
const cors = require('cors');
const path = require('path');
const mongodb = require('mongodb');

const app = express();
app.use(cors());
app.use(express.json());

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, 'public')));

const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const REDIRECT_URI = `${process.env.PROD_URL}:${process.env.PORT}/callback`;

const SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize';
const TOKEN_URL = 'https://accounts.spotify.com/api/token';

const client = new mongodb.MongoClient(process.env.MONGODB_URI, {
    serverApi: {
        version: mongodb.ServerApiVersion.v1,
        strict: true,
        deprecationErrors: true,
    }
});

const db = client.db("sinatra");

async function updateUserToken(username, tokenResponse) {
    let current_record = await getUserRecord(username)

    if (current_record) {
        await db.collection("user").updateOne({ name: username }, {
            $set: {
                token: tokenResponse.access_token,
                refresh_token: tokenResponse.refresh_token,
                expire_moment: new Date().getTime() + tokenResponse.expires_in * 1000
            }
        })
    }
    else {
        await db.collection("user").insertOne({
            name: username,
            token: tokenResponse.access_token,
            refresh_token: tokenResponse.refresh_token,
            expire_moment: new Date().getTime() + tokenResponse.expires_in * 1000
        })
    }
}

async function refreshUserToken(user) {
    const user_record = await getUserRecord(user)

    const response = await axios.post(
        TOKEN_URL,
        querystring.stringify({
            grant_type: 'refresh_token',
            refresh_token: user_record.refresh_token,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET
        }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    )

    await updateUserToken(user, response.data)
}

async function requestWithUser(user, endpoint) {
    let current_record = await getUserRecord(user)

    if (current_record.expire_moment < new Date().getTime()) {
        await refreshUserToken(user)
        current_record = await getUserRecord(user)
    }

    if (current_record) {
        const response = await axios.get(endpoint, {
            headers: { 'Authorization': `Bearer ${current_record.token}` }
        });
        return response.data;
    }
}

async function getUserRecord(user) {
    return await db.collection("user").findOne({ name: user })
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

        await updateUserToken(user.data.display_name, response.data)

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

app.listen(process.env.PORT || 8000, async () => {
    console.log('Server running on http://localhost:' + process.env.PORT);
    try {
        // Connect the client to the server
        // Send a ping to confirm a successful connection
        await client.db("admin").command({ ping: 1 });
        console.log(
            "Pinged your deployment. You successfully connected to MongoDB!"
        );
    } catch (err) {
        console.error(err);
    }
});