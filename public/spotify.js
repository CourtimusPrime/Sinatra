const base_url = `${process.env.PROD_URL}:${process.env.PORT}`

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
        return await response.json();
    } catch (error) {
        console.error("❌ Error fetching top tracks:", error);
        return [];
    }
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
        return;
    }

    trackContainer.innerHTML = topTracks.map(({ name, artists, album }, index) => `
        <div class="track">
            <div class="track-rank">#${index + 1}</div>
            <img src="${album?.images?.[0]?.url ?? 'https://i.scdn.co/image/ab6761610000517476b4b22f78593911c60e7193'}" alt="${name} album cover" class="album-cover">
            <p class="song-title">${name}</p>
            <p class="artist-name">${artists.map(a => a.name).join(', ')}</p>
        </div>
    `).join('');
}

window.onload = displayTracks;