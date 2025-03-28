// services/spotifyService.js
const axios = require('axios');
const mongodb = require('mongodb');

const client = new mongodb.MongoClient(process.env.MONGODB_URI, {
    serverApi: {
        version: mongodb.ServerApiVersion.v1,
        strict: true,
        deprecationErrors: true,
    }
});

let db;

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
        return await db.collection("user").findOne({ name: username });
    } catch (err) {
        console.error("❌ Error fetching user record:", err);
        return null;
    }
}

async function updateUserToken(username, tokenResponse) {
    try {
        const existingUser = await getUserRecord(username);

        const tokenData = {
            token: tokenResponse.access_token,
            refresh_token: tokenResponse.refresh_token,
            expire_moment: Date.now() + tokenResponse.expires_in * 1000
        };

        if (existingUser) {
            await db.collection("user").updateOne({ name: username }, { $set: tokenData });
        } else {
            await db.collection("user").insertOne({ name: username, ...tokenData });
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

module.exports = {
    connectToDatabase,
    getUserRecord,
    updateUserToken,
    requestWithUser
};