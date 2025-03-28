// routes/authRoutes.js

const express = require('express');
const router = express.Router();
const { buildAuthURL, handleSpotifyCallback } = require('../services/authService');

// Redirect to Spotify login
router.get('/login', (req, res) => {
    const authURL = buildAuthURL();
    console.log("🔗 Redirecting to Spotify Auth:", authURL);
    res.redirect(authURL);
});

// Handle Spotify callback
router.get('/callback', async (req, res) => {
    try {
        const { code } = req.query;
        const username = await handleSpotifyCallback(code);
        res.redirect(`/${encodeURIComponent(username)}`);
    } catch (error) {
        console.error("❌ Callback error:", error);
        res.status(500).send("Error logging in with Spotify.");
    }
});

module.exports = router;