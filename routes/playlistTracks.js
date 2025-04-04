const express = require('express');
const router = express.Router();
const { ObjectId } = require('mongodb');
const { getDb, getUserRecord, getTracksByISRCs } = require('../services/spotifyService');

router.get('/playlist-tracks', async (req, res) => {
    const db = getDb();
    const playlistId = req.query.id;
    const currentViewer = req.query.username;

    console.log("🎯 Incoming request to /playlist-tracks");
    console.log("🆔 Playlist ID:", playlistId);
    console.log("👤 Viewer username:", currentViewer);

    if (!playlistId || !currentViewer) {
        return res.status(400).send("Missing playlist ID or username");
    }

    try {
        const playlist = await db.collection("user_playlists").findOne({ _id: new ObjectId(playlistId) });
        if (!playlist) {
            console.error("❌ Playlist not found");
            return res.status(404).send("Playlist not found");
        }

        const viewer = await getUserRecord(currentViewer);
        if (!viewer) {
            console.error("❌ Viewer not found in DB");
        }

        const isrcs = playlist.isrcs || [];

        let tracks;

        if (!viewer || !viewer.token) {
            console.warn("⚠️ Viewer has no token, using ISRCs only");
            tracks = isrcs.map(isrc => ({ isrc }));
        } else {
            console.log("✅ Viewer has token, fetching track info");
            tracks = await getTracksByISRCs(viewer.user_id, isrcs);
        }

        return res.json({
            playlistName: playlist.name,
            playlistArt: playlist.art_url,
            totalTracks: playlist.length,
            externalUrl: playlist.external_urls?.spotify,
            tracks
        });

    } catch (err) {
        console.error("❌ /playlist-tracks error:", err);
        return res.status(500).send("Something went wrong");
    }
});

module.exports = router;