// routes/tidalRoutes.js
const express = require('express');
const router = express.Router();
const { requestWithUser } = require('../services/tidalService');

// Get current user profile (for display name / avatar / UUID)
router.get('/tidal/user', async (req, res) => {
    const { username } = req.query;
    if (!username) return res.status(400).send("Missing username");

    const data = await requestWithUser(username, `https://api.tidal.com/v1/me`);
    if (data) {
        res.json(data);
    } else {
        res.status(404).json({ error: "TIDAL user not found" });
    }
});

// Get user's top tracks — modify URL and behavior if needed
router.get('/tidal/toptracks', async (req, res) => {
    const { username } = req.query;
    if (!username) return res.status(400).send("Missing username");

    const url = `https://api.tidal.com/v1/me/favorites/tracks`; // or `me/streams/top`
    const data = await requestWithUser(username, url);

    if (data && Array.isArray(data.items)) {
        res.json(data.items);
    } else {
        res.status(404).json({ error: "No top tracks found for TIDAL user" });
    }
});

// Get user's playlists
router.get('/tidal/playlists', async (req, res) => {
    const { username } = req.query;
    if (!username) return res.status(400).send("Missing username");

    const url = `https://api.tidal.com/v1/me/playlists?limit=50`;
    const data = await requestWithUser(username, url);

    if (data && Array.isArray(data.items)) {
        res.json(data.items);
    } else {
        res.status(404).json({ error: "No playlists found for TIDAL user" });
    }
});

module.exports = router;