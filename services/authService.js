// services/authService.js

const spotifyAuth = require('./spotifyAuthService');
const tidalAuth = require('./tidalAuthService');

const authHandlers = {
  spotify: {
    buildAuthURL: spotifyAuth.buildAuthURL,
    callback: spotifyAuth.handleSpotifyCallback,
  },
  tidal: {
    buildAuthURL: tidalAuth.buildAuthURL,
    callback: tidalAuth.handleTidalCallback,
  }
};

const platform = process.env.MUSIC_PLATFORM || 'spotify';

// export only the right set of methods
const { buildAuthURL, callback: handleCallback } = authHandlers[platform];

module.exports = {
  // 👇 these are needed for platform-specific setup in authRoutes.js
  buildSpotifyAuthURL: spotifyAuth.buildAuthURL,
  handleSpotifyCallback: spotifyAuth.handleSpotifyCallback,
  buildTidalAuthURL: tidalAuth.buildAuthURL,
  handleTidalCallback: tidalAuth.handleTidalCallback,

  // 👇 these are the unified/default ones used dynamically
  buildAuthURL,
  handleCallback,
};