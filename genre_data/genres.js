async function getTopHundredGenres(uname) {
    // Fetch top 100 tracks
    const response = await fetch(`http://localhost:3000/me/top/tracks?time_range=short_term&limit=100`);
    const topTracks = await response.json();

    const artistIds = new Set();
    
    // Extract unique artist IDs from the top 100 tracks
    topTracks.forEach(track => {
        track.artists.forEach(artist => artistIds.add(artist.id));
    });

    // Convert the Set into an array and fetch artist details
    const artistIdArray = Array.from(artistIds);
    const artistResponse = await fetch(`http://localhost:3000/artists?ids=${artistIdArray.join(',')}`);
    const artistData = await artistResponse.json();

    // Extract genres from the artist data
    const genres = new Set();
    artistData.artists.forEach(artist => {
        artist.genres.forEach(genre => genres.add(genre));
    });

    return Array.from(genres); // Return unique genres
}

// Example usage:
async function displayGenres() {
    const urlSplit = window.location.href.split('/');
    const userPathString = urlSplit[urlSplit.length - 1];

    if (!userPathString) {
        document.body.innerHTML = `<a href="http://localhost:3000/login">Login with Spotify</a>`;
        return;
    }

    // Fetch and display genres
    const genres = await getTopHundredGenres(userPathString);
    document.getElementById("genre-container").innerHTML = genres.map(genre => `<p>${genre}</p>`).join('');
}

window.onload = displayGenres;