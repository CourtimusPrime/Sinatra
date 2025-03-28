// server.js

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');

const { connectToDatabase } = require('./services/spotifyService');

// Import route modules
const authRoutes = require('./routes/authRoutes');
const userRoutes = require('./routes/userRoutes');
const musicRoutes = require('./routes/musicRoutes');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// 🔒 Enforce HTTPS in production
app.use((req, res, next) => {
    if (req.headers.host.includes("localhost")) return next();
    if (req.headers["x-forwarded-proto"] !== "https") {
        return res.redirect(`https://${req.headers.host}${req.url}`);
    }
    next();
});

// 📦 Use modular routes
app.use(authRoutes);
app.use(userRoutes);
app.use(musicRoutes);

// 🌐 SPA fallback
app.get('/*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 🚀 Start server
const PORT = process.env.PORT || 3000;
const HOST = 'localhost';

app.listen(PORT, HOST, async () => {
    console.log(`🚀 Server running at http://${HOST}:${PORT}`);
    await connectToDatabase();
});