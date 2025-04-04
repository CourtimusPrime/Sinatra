// server.js
console.log("1️⃣ Starting up server...");
require('dotenv').config();
console.log("2️⃣ dotenv loaded");

const express = require('express');
console.log("3️⃣ express loaded");

const cors = require('cors');
console.log("4️⃣ cors loaded");

const path = require('path');
console.log("5️⃣ path loaded");

console.log("6️⃣ Loading routes...");
const authRoutes = require('./routes/authRoutes');
console.log("🧪 authRoutes:", typeof authRoutes);
const userRoutes = require('./routes/userRoutes');
console.log("🧪 userRoutes:", typeof userRoutes);
const musicRoutes = require('./routes/musicRoutes');
console.log("🧪 musicRoutes:", typeof musicRoutes);
const playlistTracksRouter = require('./routes/playlistTracks');
console.log("🧪 playlistTracksRouter:", typeof playlistTracksRouter);

console.log("7️⃣ Routes loaded");
const { connectToDatabase } = require('./services/spotifyService');
console.log("8️⃣ spotifyService loaded");

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

// 📦 Mount API routes before the SPA fallback
app.use(authRoutes);
app.use(userRoutes);
app.use(musicRoutes);
app.use(playlistTracksRouter); // ✅ Keep this here

// ❗️ Catch-all route for SPA paths (excluding known static files like login.html)
app.get('*', (req, res, next) => {
    if (req.path.endsWith('.html') || req.path.includes('.')) {
        return next(); // Let static middleware handle it
    }
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 🚀 Start server
const PORT = process.env.PORT || 3000;
const HOST = 'localhost';

app.listen(PORT, HOST, async () => {
    console.log(`🚀 Server running at http://${HOST}:${PORT}`);
    await connectToDatabase();
});