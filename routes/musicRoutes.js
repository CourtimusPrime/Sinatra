// routes/musicRoutes.js

const express = require('express');
const router = express.Router();
const { requestWithUser } = require('../services/spotifyService');

// Get top tracks
router.get('/toptracks', async (req, res) => {
    const { username } = req.query;
    const data = await requestWithUser(username, 'https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=3');
    data?.items ? res.json(data.items) : res.status(404).json({ error: "No Tracks Found" });
});

// Get playlists
router.get('/playlists', async (req, res) => {
    const { username } = req.query;
    const data = await requestWithUser(username, 'https://api.spotify.com/v1/me/playlists?limit=50');
    data?.items ? res.json(data.items) : res.status(404).json({ error: "No Playlists Found" });
});

module.exports = router;