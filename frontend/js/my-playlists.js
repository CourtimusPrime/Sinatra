// frontend/js/my-playlists.js

const userId = localStorage.getItem("user_id");
fetch(`/user-playlists?user_id=${userId}`)
  .then(res => res.json())
  .then(playlists => {
    // Loop and display
  });
  
if (!userId) window.location.href = "/";

async function loadPlaylists() {
  const user = await fetch(`/me?user_id=${userId}`).then(r => r.json());
  const playlistIds = user.user_playlists || [];

  const container = document.getElementById("playlist-container");
  container.innerHTML = "";

  for (const pid of playlistIds) {
    const data = await fetch(`/public-playlist/${pid}`).then(r => r.json());

    const div = document.createElement("div");
    div.innerHTML = `
      <img src="${data.image}" width="100" />
      <p><strong>${data.name}</strong></p>
    `;
    div.onclick = () => showTracks(data);
    container.appendChild(div);
  }
}

function showTracks(playlist) {
  document.getElementById("playlist-container").style.display = "none";
  document.getElementById("track-view").classList.remove("hidden");
  document.getElementById("playlist-title").textContent = playlist.name;

  const list = document.getElementById("tracks-list");
  list.innerHTML = "";

  playlist.tracks.forEach(track => {
    const item = document.createElement("div");
    item.innerHTML = `
      <p>${track.name} – ${track.artist}</p>
      <img src="${track.album_art}" width="80" />
    `;
    list.appendChild(item);
  });
}

function hideTracks() {
  document.getElementById("track-view").classList.add("hidden");
  document.getElementById("playlist-container").style.display = "grid";
  window.scrollTo(0, 0); // ← Optional, but nice UX
}

function goHome() {
  window.location.href = "/home";
}

window.onload = loadPlaylists;