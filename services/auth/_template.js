// services/auth/_template.js

/**
 * Template for creating a new music auth platform.
 * Rename this file and update logic accordingly.
 */

function buildAuthURL(req) {
    // If your auth flow needs session or req context, keep the param.
    // Otherwise, make this a pure function.
    return `https://platform.com/authorize?client_id=CLIENT_ID&redirect_uri=REDIRECT_URI`;
  }
  
  async function handleCallback(reqOrCode, maybeCode) {
    // If you passed `req` and `code`, destructure like:
    const req = maybeCode ? reqOrCode : null;
    const code = maybeCode || reqOrCode;
  
    // Exchange `code` for access token
    // Use token to get user info
    // Save user/token in DB
    return 'username_or_userId';
  }
  
  module.exports = {
    buildAuthURL,
    handleCallback
  };