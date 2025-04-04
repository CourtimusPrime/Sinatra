// routes/userRoutes.js
const express = require('express');
const router = express.Router();
const { requestWithUser } = require('../services/spotifyService');

// Get public user profile by username (Spotify ID)
router.get('/user', async (req, res) => {
    const { username } = req.query;
    
    if (!username) return res.status(400).send("Missing username");

    try {
        const data = await requestWithUser(username, `https://api.spotify.com/v1/users/${username}`);
        data ? res.json(data) : res.status(404).send("User not found");
    } catch (err) {
        console.error("❌ Error fetching user:", err);
        res.status(500).send("Something went wrong");
    }
});

module.exports = router;