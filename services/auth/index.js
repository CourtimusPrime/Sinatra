// services/auth/index.js

require('dotenv').config();
const spotify = require('./spotify');
const tidal = require('./tidal');

const platforms = {
  spotify: {
    name: "Spotify",
    icon: "/png/spotify.png",
    buildAuthURL: spotify.buildAuthURL,
    handleCallback: spotify.handleCallback,
    needsRequest: false,
    color: "rgba(30,215,96,1)"
  },
  tidal: {
    name: "Tidal",
    icon: "/png/tidal.png",
    buildAuthURL: tidal.buildAuthURL,
    handleCallback: tidal.handleCallback,
    needsRequest: true,
    color:"rgba(0,0,0,0)"
  },
  // future:
  // apple: { ... },
  // youtube: { ... }
};

const getPlatform = (platformName = process.env.MUSIC_PLATFORM || 'spotify') => {
  const key = platformName.toLowerCase();
  const selected = platforms[key];
  if (!selected) {
    console.error(`❌ Unsupported music platform requested: "${platformName}"`);
    throw new Error(`Unsupported music platform: ${platformName}`);
  }
  console.log(`🎵 Using platform: ${selected.name} ${selected.icon}`);
  return selected;
};

const listSupportedPlatforms = () => Object.keys(platforms);

module.exports = {
  getPlatform,
  platforms, // 🔍 for introspection or UI
  listSupportedPlatforms
};