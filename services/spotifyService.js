// services/spotifyService.js
const axios = require('axios');
const mongodb = require('mongodb');
let db;

const client = new mongodb.MongoClient(process.env.MONGODB_URI, {
    serverApi: {
        version: mongodb.ServerApiVersion.v1,
        strict: true,
        deprecationErrors: true,
    }
});

async function connectToDatabase() {
    try {
        await client.connect();
        db = client.db("sinatra");
        await db.command({ ping: 1 });
        console.log("✅ Connected to MongoDB");
    } catch (err) {
        console.error("❌ MongoDB connection error:", err);
    }
}

async function getUserRecord(username) {
    try {
        return await db.collection("user").findOne({ user_id: username });
    } catch (err) {
        console.error("❌ Error fetching user record:", err);
        return null;
    }
}

const storeUserPlaylists = async (userId, accessToken) => {
    try {
        const response = await axios.get(`https://api.spotify.com/v1/users/${userId}/playlists?limit=50`, {
            headers: { Authorization: `Bearer ${accessToken}` }
        });

        const playlists = response.data.items;
        const collection = db.collection('user_playlists');

        await collection.deleteMany({ user_id: userId });

        for (const playlist of playlists) {
            // Fetch the tracks from the playlist
            const tracksRes = await axios.get(playlist.tracks.href, {
                headers: { Authorization: `Bearer ${accessToken}` }
            });

            const isrcs = tracksRes.data.items
                .map(item => item.track?.external_ids?.isrc)
                .filter(Boolean);

            const playlistDoc = {
                name: playlist.name,
                user_id: userId,
                art_url: playlist.images?.[0]?.url || "https://via.placeholder.com/100",
                description: playlist.description || "",
                length: playlist.tracks?.total || 0,
                isrcs: isrcs,
                isrc_string: isrcs.join(','), // ✅ new field
                external_urls: playlist.external_urls
            };

            await collection.updateOne(
                { user_id: userId, spotify_id: playlist.id }, // match by user + playlist
                { $set: playlistDoc },                        // update all fields
                { upsert: true }                              // insert if not found
              );
        }

        console.log(`✅ Stored ${playlists.length} playlists for user ${userId}`);
    } catch (err) {
        console.error("❌ Error storing user playlists:", err.message);
    }
};

async function updateUserToken(username, tokenResponse) {
    try {
        const existingUser = await getUserRecord(username);

        const tokenData = {
            token: tokenResponse.access_token,
            refresh_token: tokenResponse.refresh_token,
            expire_moment: Date.now() + tokenResponse.expires_in * 1000
        };

        if (existingUser) {
            await db.collection("user").updateOne({ user_id: username }, { $set: tokenData });
        } else {
            await db.collection("user").insertOne({ user_id: username, ...tokenData });
        }

        console.log(`✅ Updated tokens for user: ${username}`);
    } catch (err) {
        console.error("❌ Error updating token:", err);
    }
}

async function requestWithUser(username, url) {
    try {
        const user = await getUserRecord(username);
        if (!user || !user.token) return null;

        const response = await axios.get(url, {
            headers: { Authorization: `Bearer ${user.token}` },
        });

        return response.data || null;
    } catch (err) {
        console.error("❌ requestWithUser error:", err);
        return null;
    }
}
function getDb() {
    return db;
}

const getTracksByISRCs = async (username, isrcs = []) => {
    if (!isrcs.length) return [];

    const user = await getUserRecord(username);
    if (!user?.token) return [];

    const headers = {
        Authorization: `Bearer ${user.token}`
    };

    const results = [];

    for (const isrc of isrcs) {
        try {
            const res = await axios.get(`https://api.spotify.com/v1/search?q=isrc:${isrc}&type=track`, { headers });
            const track = res.data.tracks?.items?.[0];
            if (track) {
                results.push({
                    name: track.name,
                    artist: track.artists.map(a => a.name).join(', '),
                    album: track.album.name,
                    preview_url: track.preview_url,
                    isrc,
                    spotify_url: track.external_urls.spotify,
                    image: track.album.images?.[0]?.url || null
                });
            }
        } catch (err) {
            console.warn(`❌ Failed to fetch track for ISRC ${isrc}:`, err.message);
        }
    }

    return results;
};

module.exports = {
    connectToDatabase,
    getUserRecord,
    updateUserToken,
    requestWithUser,
    storeUserPlaylists,
    getDb,
    getTracksByISRCs
};