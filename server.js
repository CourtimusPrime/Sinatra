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

app.use(express.static(path.join(__dirname, 'public')));

app.use((req, res, next) => {
    if (req.headers.host.includes("localhost")) {
        return next(); // Do not enforce HTTPS on localhost
    }
    if (req.headers["x-forwarded-proto"] !== "https") {
        return res.redirect(`https://${req.headers.host}${req.url}`);
    }
    next();
});

const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;

const REDIRECT_URI = process.env.NODE_ENV === "production" ? `${process.env.PROD_URL}/callback` : "http://localhost:3000/callback";

const SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize';
const TOKEN_URL = 'https://accounts.spotify.com/api/token';

const client = new mongodb.MongoClient(process.env.MONGODB_URI, {
    serverApi: {
        version: mongodb.ServerApiVersion.v1,
        strict: true,
        deprecationErrors: true,
    }
});

let db;

// 🔹 Connect to MongoDB on Server Start
async function connectToDatabase() {
    try {
        await client.connect();
        db = client.db("sinatra");
        await db.command({ ping: 1 });
        console.log("✅ Successfully connected to MongoDB!");
    } catch (error) {
        console.error("❌ MongoDB connection error:", error);
    }
}

// 🔹 Login Route - Redirects to Spotify
app.get('/login', (req, res) => {
    const scope = 'user-top-read';

    // Debugging output before redirection
    console.log("🔍 CLIENT_ID:", CLIENT_ID);
    console.log("🔍 REDIRECT_URI:", REDIRECT_URI);
    console.log("🔍 SPOTIFY_AUTH_URL Before Encoding:", SPOTIFY_AUTH_URL);

    const authURL = `${SPOTIFY_AUTH_URL}?response_type=code&client_id=${CLIENT_ID}&scope=${encodeURIComponent(scope)}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}`;

    console.log("🔗 Final Authorization URL:", authURL); // Debug final redirect URL

    res.redirect(authURL);
});

// 🔹 Callback Route - Handles Spotify Auth Response
app.get('/callback', async (req, res) => {
    const { code } = req.query;
    try {
        if (!code) throw new Error("Missing authorization code.");

        console.log('🔑 Authorization code received:', code);

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

        console.log('✅ Access token response:', response.data);

        // Fetch user details
        const user = await axios.get('https://api.spotify.com/v1/me', {
            headers: { 'Authorization': `Bearer ${response.data.access_token}` }
        });

        console.log('👤 User data:', user.data);

        // Store token
        await updateUserToken(user.data.display_name, response.data);

        // Redirect user to their profile
        res.redirect(`/${encodeURIComponent(user.data.display_name)}`);
    } catch (error) {
        console.error('❌ Error during token exchange:', error);
        res.status(500).send('Error logging in with Spotify.');
    }
});

// 🔹 Function to Get User Record from MongoDB
async function getUserRecord(username) {
    try {
        const userRecord = await db.collection("user").findOne({ name: username });
        return userRecord;
    } catch (error) {
        console.error("❌ Error fetching user record:", error);
        return null;
    }
}

// 🔹 Function to Get User Record from MongoDB
async function getUserRecord(username) {
    try {
        const userRecord = await db.collection("user").findOne({ name: username });
        return userRecord;
    } catch (error) {
        console.error("❌ Error fetching user record:", error);
        return null;
    }
}

// 🔹 Function to Update or Insert User Token in MongoDB
async function updateUserToken(username, tokenResponse) {
    try {
        let current_record = await getUserRecord(username);

        if (current_record) {
            await db.collection("user").updateOne(
                { name: username },
                {
                    $set: {
                        token: tokenResponse.access_token,
                        refresh_token: tokenResponse.refresh_token,
                        expire_moment: Date.now() + tokenResponse.expires_in * 1000
                    }
                }
            );
        } else {
            await db.collection("user").insertOne({
                name: username,
                token: tokenResponse.access_token,
                refresh_token: tokenResponse.refresh_token,
                expire_moment: Date.now() + tokenResponse.expires_in * 1000
            });
        }
        console.log(`✅ Updated tokens for user: ${username}`);
    } catch (error) {
        console.error("❌ Error updating user token:", error);
    }
}

// 🔹 Fetch User Profile Data
app.get('/user', async (req, res) => {
    const userData = await requestWithUser(req.query.username, 'https://api.spotify.com/v1/me');
    userData ? res.send(userData) : res.status(404).send("Invalid User");
});

// 🔹 Fetch User's Top Tracks
app.get('/toptracks', async (req, res) => {
    try {
        console.log(`🔍 Fetching top tracks for user: ${req.query.username}`);
        
        const tracks = await requestWithUser(
            req.query.username,
            'https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=3'
        );

        if (!tracks || !tracks.items) {
            console.error("❌ No top tracks found or invalid response format:", tracks);
            return res.status(404).json({ error: "Invalid User or No Tracks Found" });
        }

        res.json(tracks.items);
    } catch (error) {
        console.error("❌ Error fetching top tracks:", error);
        res.status(500).json({ error: "Internal server error", details: error.message });
    }
});

async function requestWithUser(username, url) {
    try {
        console.log(`🔗 Making request to Spotify API for ${username}: ${url}`);

        // Fetch user from MongoDB
        const user = await getUserRecord(username);
        if (!user || !user.token) {
            console.error("❌ User not found or missing access token:", user);
            return null;
        }

        // Make the request to Spotify API with the user's token
        const response = await axios.get(url, {
            headers: { Authorization: `Bearer ${user.token}` },
        });

        if (!response.data) {
            console.error("❌ No data received from Spotify API");
            return null;
        }

        return response.data;
    } catch (error) {
        console.error("❌ Error in requestWithUser:", error);
        return null;
    }
}

// 🔹 Fetch User's Playlists
app.get('/playlists', async (req, res) => {
    try {
        const playlists = await requestWithUser(
            req.query.username,
            'https://api.spotify.com/v1/me/playlists?limit=50'
        );

        if (!playlists || !playlists.items) {
            console.error("❌ No playlists found or invalid response format:", playlists);
            return res.status(404).json({ error: "No Playlists Found or Invalid User" });
        }

        res.json(playlists.items);
    } catch (error) {
        console.error("❌ Error fetching playlists:", error);
        res.status(500).json({ error: "Internal server error", details: error.message });
    }
});

// 🔹 Catch-All Route for Frontend SPA
app.get('/*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 🔹 Start Server & Connect to MongoDB
const PORT = process.env.PORT || 3000;
// Change HOST to 'localhost' to ensure it runs locally
const HOST = 'localhost';

app.listen(PORT, HOST, async () => {
    console.log(`🚀 Server running on http://${HOST}:${PORT}`);
    await connectToDatabase();
});