//routes/userRoutes.js
const express = require('express');
const router = express.Router();
const { requestWithUser } = require('../services/spotifyService');

// Get user profile info
router.get('/user', async (req, res) => {
    const { username } = req.query;
    const data = await requestWithUser(username, 'https://api.spotify.com/v1/me');
    data ? res.send(data) : res.status(404).send("Invalid User");
});

module.exports = router;