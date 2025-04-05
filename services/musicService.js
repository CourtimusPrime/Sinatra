// services/musicService.js

const spotifyService = require('./spotifyService');
const tidalService = require('./tidalService');

const getActiveService = () => {
    const platform = process.env.MUSIC_PLATFORM || 'spotify';
    return platform === 'tidal' ? tidalService : spotifyService;
};

module.exports = getActiveService();