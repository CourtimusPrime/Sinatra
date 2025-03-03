async function getSpotifyUser(token) {
    const response = await fetch('https://api.spotify.com/v1/me', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    return await response.json();
}

async function getTopTracks(token) {
    const response = await fetch('https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=5', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    return (await response.json()).items;
}

async function displayTracks() {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('access_token');

    if (!accessToken) {
        document.body.innerHTML = `<a href="http://localhost:3000/login">Login with Spotify</a>`;
        return;
    }

    // Fetch user info
    const user = await getSpotifyUser(accessToken);
    const username = user.display_name || "Spotify User"; // Fallback if no name is available

    // Find the header element
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) {
        pageTitle.innerText = `${username}'s Top Tracks This Month`;
    } else {
        console.error("Element with ID 'page-title' not found.");
    }

    // Fetch top tracks
    const topTracks = await getTopTracks(accessToken);
    const trackContainer = document.getElementById('track-container');

    trackContainer.innerHTML = topTracks.map(({ name, artists, album }) => `
        <div class="track">
            <img src="${album.images[0].url}" alt="${name} album cover" class="album-cover">
            <p class="song-title">${name}</p>
            <p class="artist-name">${artists.map(a => a.name).join(', ')}</p>
        </div>
    `).join('');
}

window.onload = displayTracks;