// frontend/js/home.js
const userId = localStorage.getItem("user_id");
if (!userId) {
  window.location.href = "/";
}

async function loadUser() {
  const user = await fetch(`/me?user_id=${userId}`).then(r => r.json());

  document.getElementById("user-name").textContent = user.display_name;
  document.getElementById("profile-pic").src = user.profile_picture;

  const featured = user.important_playlists || [];
  const playlistContainer = document.getElementById("featured-playlists");

  for (const playlistId of featured) {
    const res = await fetch(`/playlist-info?user_id=${userId}&playlist_id=${playlistId}`);
    const data = await res.json();

    const div = document.createElement("div");
    div.innerHTML = `
      <p><strong>${data.name}</strong></p>
      <img src="${data.image}" width="100" />
    `;
    playlistContainer.appendChild(div);
  }
}

async function loadNowPlaying() {
  const playback = await fetch(`/playback?user_id=${userId}`).then(r => r.json());
  if (playback.playback && playback.playback.track) {
    document.getElementById("track-name").textContent = playback.playback.track.name + " – " + playback.playback.track.artist;
    document.getElementById("track-art").src = playback.playback.track.album_art_url || "/static/default-cover.jpg";
  }
}

function logout() {
  localStorage.clear();
  window.location.href = "/";
}

// Call loadNowPlaying every 30 seconds
setInterval(loadNowPlaying, 30000);

window.onload = () => {
  loadUser();
  loadNowPlaying();
};