const base_url = window.location.origin;

async function getSpotifyUser(uname) {
    try {
        const response = await fetch(`${base_url}/user?username=${uname}`);
        if (!response.ok) throw new Error("Failed to fetch user data");
        return await response.json();
    } catch (error) {
        console.error("❌ Error fetching user data:", error);
        return null;
    }
}

async function getTopTracks(uname) {
    try {
        const response = await fetch(`${base_url}/toptracks?username=${uname}`);
        if (!response.ok) throw new Error("Failed to fetch top tracks");
        
        const data = await response.json();
        if (!Array.isArray(data)) throw new Error("Invalid API response format");

        return data;
    } catch (error) {
        console.error("❌ Error fetching top tracks:", error);
        return [];
    }
}

async function getUserPlaylists(uname) {
    try {
        const response = await fetch(`${base_url}/playlists?username=${uname}`);
        const text = await response.text(); // Read as plain text
        console.log("📦 Raw playlist response:", text);

        // Try to parse if it's JSON
        try {
            return JSON.parse(text);
        } catch (jsonError) {
            console.error("❌ Not valid JSON. Probably HTML fallback.");
            return [];
        }
    } catch (error) {
        console.error("❌ Error fetching playlists:", error);
        return [];
    }
}

let allPlaylists = []; // store them globally so we can search later

function displayPlaylists(filteredPlaylists) {
    const container = document.getElementById('playlist-container');
    container.innerHTML = ''; // clear old results

    if (filteredPlaylists.length === 0) {
        container.style.display = 'none';
        return;
    }

    // Show the container only when there's something to show
    container.style.display = 'block';

    container.innerHTML = filteredPlaylists.map(pl => `
        <div class="playlist" data-name="${pl.name.toLowerCase()}">
            <img src="${pl.images?.[0]?.url ?? 'https://via.placeholder.com/60'}" alt="Playlist Cover" class="playlist-cover">
            <p class="playlist-name">${pl.name}</p>
        </div>
    `).join('');
}

function setupPlaylistSearch() {
    const searchBar = document.getElementById('search-bar');
    const container = document.getElementById('playlist-container');

    // Hide container by default
    container.style.display = 'none';

    searchBar.addEventListener('input', () => {
        const query = searchBar.value.toLowerCase();

        if (!query) {
            displayPlaylists([]); // clear display if input is empty
            return;
        }

        const filtered = allPlaylists.filter(pl =>
            pl.name.toLowerCase().includes(query)
        );

        displayPlaylists(filtered);
    });
}

async function displayTracks() {
    const urlSplit = window.location.href.split('/');
    const userPathString = urlSplit[urlSplit.length - 1] || null;

    if (!userPathString) {
        document.body.innerHTML = `<a href="${base_url}/login">Login with Spotify</a>`;
        return;
    }

    // Fetch user info
    const user = await getSpotifyUser(userPathString);

    if (!user) {
        document.body.innerHTML = `<h2>User not found. <a href="${base_url}/login">Login with Spotify</a></h2>`;
        return;
    }

    const username = user?.display_name || "John Doe";
    const profilePic = user?.images?.[0]?.url ?? "https://i.scdn.co/image/ab6761610000517476b4b22f78593911c60e7193";

    // Update UI
    document.querySelector("h1").innerText = `${username}'s Top Tracks This Month`;
    document.getElementById("profile-pic").setAttribute("src", profilePic);

    // Fetch top tracks
    const topTracks = await getTopTracks(userPathString);
    const trackContainer = document.getElementById('track-container');

    if (topTracks.length === 0) {
        trackContainer.innerHTML = `<p>No top tracks available.</p>`;
    } else {
        trackContainer.innerHTML = topTracks.map(({ name, artists, album }, index) => `
            <div class="track">
                <div class="track-rank">#${index + 1}</div>
                <img src="${album?.images?.[0]?.url ?? 'https://i.scdn.co/image/ab6761610000517476b4b22f78593911c60e7193'}" alt="${name} album cover" class="album-cover">
                <p class="song-title">${name}</p>
                <p class="artist-name">${artists.map(a => a.name).join(', ')}</p>
            </div>
        `).join('');
    }

    // ✅ Fetch and display playlists + set up search
    const playlists = await getUserPlaylists(userPathString);
    displayPlaylists(playlists);
    allPlaylists = await getUserPlaylists(userPathString);
    setupPlaylistSearch();
}

window.onload = displayTracks;