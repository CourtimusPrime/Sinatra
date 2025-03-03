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

    const topTracks = await getTopTracks(accessToken);
    const trackList = topTracks.map(({ name, artists, album }) =>
        `<li>
            <img src="${album.images[0].url}" alt="${name} album cover" width="50">
            ${name} by ${artists.map(a => a.name).join(', ')}
        </li>`
    ).join('');

    document.getElementById('track-list').innerHTML = trackList;
}

window.onload = displayTracks;