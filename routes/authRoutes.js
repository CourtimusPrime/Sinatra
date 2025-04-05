// routes/authRoutes.js
const express = require('express');
const router = express.Router();
const { getPlatform } = require('../services/auth');

// 🌐 Universal login route (used after /login/spotify or /login/tidal)
router.get('/login', (req, res) => {
  try {
    const platform = req.query.platform || process.env.MUSIC_PLATFORM || 'spotify';
    const { buildAuthURL, needsRequest } = getPlatform(platform);

    console.log(`🔐 Login initiated for platform: ${platform}`);

    // ✅ First define the URL
    const url = needsRequest ? buildAuthURL(req) : buildAuthURL();

    // ✅ Then log it
    console.log("🌐 Redirecting to:", url);

    res.redirect(url);
  } catch (err) {
    console.error("❌ Login error:", err.message);
    res.status(500).send("Login setup failed.");
  }
});

// 🎧 Quick redirect helpers
router.get('/login/spotify', (req, res) => {
  console.log("🎧 Redirecting to Spotify login...");
  res.redirect('/login?platform=spotify');
});

router.get('/login/tidal', (req, res) => {
  console.log("🌊 Redirecting to TIDAL login...");
  res.redirect('/login?platform=tidal'); // Let /login handle the URL generation
});


const { platforms } = require('../services/auth');

// For front-end to fetch available platforms
router.get('/platforms', (req, res) => {
  const result = Object.entries(platforms).map(([key, config]) => ({
    id: key,
    name: config.name,
    icon: config.icon
  }));
  res.json(result);
});

// ⏪ OAuth callback
router.get('/callback', async (req, res) => {
  try {
    const platform = req.query.state || req.query.platform || process.env.MUSIC_PLATFORM || 'spotify';
    const { handleCallback, needsRequest } = getPlatform(platform);

    const { code } = req.query;
    if (!code) return res.status(400).send("Missing authorization code.");

    console.log(`🔁 Callback received for platform: ${platform}`);

    const username = needsRequest
      ? await handleCallback(req, code)
      : await handleCallback(code);

    console.log(`✅ Authenticated ${platform} user: ${username}`);
    res.redirect(`/${encodeURIComponent(username)}`);
  } catch (err) {
    console.error("❌ Callback error:", err.message);
    res.status(500).send("Callback failed.");
  }
});

module.exports = router;