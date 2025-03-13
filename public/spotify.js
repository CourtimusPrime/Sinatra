async function getSpotifyUser(uname) {
    const response = await fetch(`http://localhost:3000/user?username=${uname}`)
    return await response.json();
}

async function getTopTracks(uname) {
    const response = await fetch(`http://localhost:3000/toptracks?username=${uname}`)
    return await response.json();
}

async function getTopGenres(uname) {
    const response = await fetch(`http://localhost:3000/toptracks?username=${uname}&time_range=short_term&limit=100`);
    const topTracks = await response.json();

    const genres = new Set();
    for (const track of topTracks) {
        const trackResponse = await fetch(`http://localhost:3000/track?track_id=${track.id}`);
        const trackData = await trackResponse.json();
        trackData.genres.forEach(genre => genres.add(genre));
    }

    return Array.from(genres);
}

async function displayTracks() {
    //const params = new URLSearchParams(window.location.search);
    const urlSplit = window.location.href.split('/')
    //const accessToken = params.get('access_token');

    const userPathString = urlSplit[urlSplit.length - 1]

    if (!userPathString) {
        document.body.innerHTML = `<a href="http://localhost:3000/login">Login with Spotify</a>`;
        return;
    }
    else {
        // Fetch user info
        const user = await getSpotifyUser(userPathString);
        const username = user.display_name || "Spotify User"; // Fallback if no name is available
        const profilePic = user.images[0]?.url; // Get profile picture URL

        // Update the page title dynamically
        document.querySelector("h1").innerText = `${username}'s Top Tracks This Month`;

        // Display profile picture or default pic
        document.getElementById("profile-pic").setAttribute("src", profilePic ?? "https://i.scdn.co/image/ab6761610000517476b4b22f78593911c60e7193")

        // Fetch top tracks
        const topTracks = await getTopTracks(userPathString);
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
}

async function displayGenres() {
    const urlSplit = window.location.href.split('/');
    const userPathString = urlSplit[urlSplit.length - 1];

    if (userPathString) {
        const genres = await getTopGenres(userPathString);
        const genreList = document.getElementById('genre-list');
        genreList.innerHTML = genres.map(genre => `<li>${genre}</li>`).join('');
    }
}

window.onload = () => {
    displayTracks();
    displayGenres();
};