// routes/musicRoutes.js
const path = require('path');
const express = require('express');
const router = express.Router();
const { requestWithUser } = require('../services/spotifyService');
const spotifyService = require("../services/spotifyService");

// Get top tracks
router.get('/toptracks', async (req, res) => {
    const { username } = req.query;
    const data = await requestWithUser(username, 'https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=3');
    data?.items ? res.json(data.items) : res.status(404).json({ error: "No Tracks Found" });
});

// Get stored playlists from MongoDB
router.get("/stored-playlists", async (req, res) => {
    const username = req.query.username;
    if (!username) return res.status(400).json({ error: "Username is required" });

    try {
        const db = spotifyService.getDb(); // 👈 now it works!
        const playlists = await db.collection("user_playlists").find({ user_id: username }).toArray();
        res.json(playlists);
    } catch (err) {
        console.error("❌ Error fetching stored playlists:", err);
        res.status(500).json({ error: "Error fetching stored playlists" });
    }
});

// Get playlists
router.get('/playlists', async (req, res) => {
    const { username } = req.query;
    console.log("📥 Playlist request for username:", username); // <--- Log this
    const limit = req.query.limit || 50;
    const url = `https://api.spotify.com/v1/users/${username}/playlists?limit=${limit}`;
    const data = await requestWithUser(username, url);

    console.log("📤 Spotify response:", JSON.stringify(data, null, 2)); // <--- Debug here

    if (data?.items) {
        res.json(data.items);
    } else {
        res.status(404).json({ error: "No Playlists Found" });
    }
});

// Render all playlists page
router.get('/playlists/view', async (req, res) => {
    res.sendFile(path.join(__dirname, '../public/playlists.html'));
});

module.exports = router;