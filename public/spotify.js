const base_url = window.location.origin;

let userPlaylists = [];

async function getUserPlaylists(username) {
    try {
        const response = await fetch(`${base_url}/playlists?username=${username}`);
        if (!response.ok) throw new Error("Failed to fetch playlists");

        const data = await response.json();
        if (!Array.isArray(data)) throw new Error("Invalid playlist response format");

        userPlaylists = data;
        console.log("🎵 User playlists loaded:", userPlaylists);
    } catch (error) {
        console.error("❌ Error fetching playlists:", error);
    }
}

function setupSearchBar() {
    const searchBar = document.getElementById("search-bar");

    if (!searchBar) {
        console.error("❌ No search bar found in DOM.");
        return;
    }

    searchBar.addEventListener("input", () => {
        const resultsContainer = document.getElementById("playlist-results");

        if (!resultsContainer) {
            console.error("❌ No #playlist-results container found in DOM.");
            return;
        }

        const searchTerm = searchBar.value.toLowerCase();
        const filtered = userPlaylists.filter(p =>
            p.name.toLowerCase().includes(searchTerm)
        );

        resultsContainer.innerHTML = "";

        filtered.forEach(playlist => {
            const div = document.createElement("div");
            div.className = "playlist-result";
            div.style.display = "flex";
            div.style.alignItems = "center";
            div.style.cursor = "pointer";
            div.style.marginBottom = "10px";
            div.style.padding = "5px";
            div.style.border = "1px solid #ddd";
            div.style.borderRadius = "6px";
            div.style.backgroundColor = "#fff";
            div.style.boxShadow = "0 1px 3px rgba(0,0,0,0.1)";
        
            // 🎵 Playlist Image
            const img = document.createElement("img");
            img.src = playlist.images?.[0]?.url || "https://via.placeholder.com/50";
            img.alt = playlist.name;
            img.style.width = "50px";
            img.style.height = "50px";
            img.style.objectFit = "cover";
            img.style.borderRadius = "4px";
            img.style.marginRight = "12px";
        
            // 📛 Playlist Name
            const name = document.createElement("span");
            name.textContent = playlist.name;
            name.style.fontSize = "16px";
            name.style.fontWeight = "500";
            name.style.color = "black";
        
            div.appendChild(img);
            div.appendChild(name);
        
            div.onclick = () => addPlaylistToList(playlist);
        
            resultsContainer.appendChild(div);
        });
    });
}

function addPlaylistToList(playlist) {
    const list = document.getElementById("playlist-list");

    // Prevent duplicates
    if ([...list.children].some(li => li.dataset.id === playlist.id)) return;

    const li = document.createElement("li");
    li.dataset.id = playlist.id;
    li.style.display = "flex";
    li.style.alignItems = "center";
    li.style.marginBottom = "10px";

    // Image
    const img = document.createElement("img");
    img.src = playlist.images?.[0]?.url || "https://via.placeholder.com/50";
    img.alt = playlist.name;
    img.style.width = "40px";
    img.style.height = "40px";
    img.style.borderRadius = "4px";
    img.style.marginRight = "10px";
    img.style.objectFit = "cover";

    // Name
    const name = document.createElement("span");
    name.textContent = playlist.name;
    name.style.fontSize = "16px";

    li.appendChild(img);
    li.appendChild(name);

    list.appendChild(li);
}

async function displayTracks() {
    const urlSplit = window.location.href.split('/');
    const userPathString = urlSplit[urlSplit.length - 1] || null;

    if (!userPathString) {
        document.body.innerHTML = `<a href="${base_url}/login">Login with Spotify</a>`;
        return;
    }

    const user = await getSpotifyUser(userPathString);

    if (!user) {
        document.body.innerHTML = `<h2>User not found. <a href="${base_url}/login">Login with Spotify</a></h2>`;
        return;
    }

    document.getElementById("username").innerText = user.display_name || "User";

    const topTracks = await getTopTracks(userPathString);
    const trackContainer = document.getElementById("track-container");

    trackContainer.innerHTML = topTracks.map(({ name, artists, album }, i) => `
    <div class="track">
        <div class="track-rank">#${i + 1}</div>
        <img src="${album?.images?.[0]?.url ?? 'https://via.placeholder.com/150'}" class="album-cover" alt="${name} album cover" />
        <div class="track-info">
            <p class="song-title">${name}</p>
            <p class="artist-name">${artists.map(a => a.name).join(', ')}</p>
        </div>
    </div>
`).join('');

    // 💡 This is the key part
    await getUserPlaylists(userPathString);
    setupSearchBar();
}

// You also need these:
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

window.onload = () => {
    displayTracks();
  };