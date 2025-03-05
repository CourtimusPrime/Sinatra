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
    const profilePic = user.images[0]?.url; // Get profile picture URL

    // Update the page title dynamically
    document.querySelector("h1").innerText = `${username}'s Top Tracks This Month`;

    // Display profile picture or default pic
    document.getElementById("profile-pic").setAttribute("src", profilePic ?? "https://i.scdn.co/image/ab6761610000517476b4b22f78593911c60e7193")

    // Fetch top tracks
    const topTracks = await getTopTracks(accessToken);
    const trackContainer = document.getElementById('track-container');

    // Display tracks with ranking numbers
    trackContainer.innerHTML = topTracks.map(({ name, artists, album }, index) => `
        <div class="track">
            <div class="track-rank">#${index + 1}</div>
            <img src="${album.images[0].url}" alt="${name} album cover" class="album-cover">
            <p class="song-title">${name}</p>
            <p class="artist-name">${artists.map(a => a.name).join(', ')}</p>
        </div>
    `).join('');
}

window.onload = displayTracks;