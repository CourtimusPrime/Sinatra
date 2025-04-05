// services/tidalService.js
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
        console.log("✅ Connected to MongoDB (TIDAL)");
    } catch (err) {
        console.error("❌ MongoDB connection error (TIDAL):", err);
    }
}

function getDb() {
    return db;
}

// Generates code verifier and challenge for PKCE
function generatePKCECodes() {
    const codeVerifier = base64URLEncode(crypto.randomBytes(64));
    const codeChallenge = base64URLEncode(
        crypto.createHash('sha256').update(codeVerifier).digest()
    );
    return { codeVerifier, codeChallenge };
}

function base64URLEncode(buffer) {
    return buffer.toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
}

async function getUserRecord(userId) {
    try {
        return await db.collection("tidal_users").findOne({ user_id: userId });
    } catch (err) {
        console.error("❌ Error fetching TIDAL user record:", err);
        return null;
    }
}

async function updateUserToken(userId, tokenData) {
    const tokenPayload = {
        token: tokenData.access_token,
        refresh_token: tokenData.refresh_token,
        expire_moment: Date.now() + tokenData.expires_in * 1000
    };

    const existingUser = await getUserRecord(userId);

    try {
        if (existingUser) {
            await db.collection("tidal_users").updateOne({ user_id: userId }, { $set: tokenPayload });
        } else {
            await db.collection("tidal_users").insertOne({ user_id: userId, ...tokenPayload });
        }

        console.log(`✅ Updated TIDAL tokens for user: ${userId}`);
    } catch (err) {
        console.error("❌ Error updating TIDAL token:", err);
    }
}

async function requestWithUser(userId, url) {
    const user = await getUserRecord(userId);
    if (!user || !user.token) {
        console.warn("⚠️ No token found for TIDAL user:", userId);
        return null;
    }

    try {
        const response = await axios.get(url, {
            headers: {
                Authorization: `Bearer ${user.token}`
            }
        });

        return response.data || null;
    } catch (err) {
        console.error("❌ requestWithUser (TIDAL) error:", err.message);
        return null;
    }
}

module.exports = {
    connectToDatabase,
    getDb,
    getUserRecord,
    updateUserToken,
    requestWithUser,
    MUSIC_PLATFORM: process.env.MUSIC_PLATFORM
};