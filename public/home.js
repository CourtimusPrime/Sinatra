const urlParams = new URLSearchParams(window.location.search);
const queryUsername = urlParams.get("username");
const username = queryUsername || localStorage.getItem("username");

if (!username) {
  alert("Username missing — please log in again.");
  window.location.href = "/login";
}

async function loadHome() {
  const tracksRes = await fetch(`/toptracks?username=${username}`);
  const tracks = await tracksRes.json();

  const userRes = await fetch(`/user?username=${username}`);
  const user = await userRes.json();

  // Save username for future visits
  localStorage.setItem("username", username);

  // Top tracks
  document.getElementById("top-tracks").innerHTML = tracks.slice(0, 3).map(track => `
    <div class="track">
      <img src="${track.album.images?.[0]?.url ?? 'https://via.placeholder.com/60'}" />
      <p>${track.name} — ${track.artists.map(a => a.name).join(", ")}</p>
    </div>
  `).join("");

  // Featured playlists
  document.getElementById("featured-playlists").innerHTML = user.featured_playlists.map(pl => `
    <div class="playlist">
      <a href="https://open.spotify.com/playlist/${pl.id}" target="_blank">
        <img src="${pl.image}" />
        <p>${pl.name}</p>
      </a>
    </div>
  `).join("");

  // User profile
  document.getElementById("username").innerText = `Welcome, ${user.display_name || username}`;
  document.getElementById("user-pic").src = user.images?.[0]?.url ?? "https://via.placeholder.com/100";
}

loadHome();

// Modal logic for editing playlists
const modal = document.getElementById('edit-modal');
const openBtn = document.getElementById('edit-playlists-btn');
const closeBtn = document.getElementById('close-modal');
const saveBtn = document.getElementById('save-featured-btn');
const modalContainer = document.getElementById('modal-playlist-list');

let modalSelected = [];
let allPlaylists = [];

openBtn.addEventListener('click', async () => {
  modal.style.display = 'block';
  saveBtn.disabled = true;
  modalSelected = [];

  const res = await fetch(`/playlists?username=${username}`);
  allPlaylists = await res.json();

  modalContainer.innerHTML = allPlaylists.map(pl => `
    <div class="playlist" data-id="${pl.id}" data-name="${pl.name}" data-img="${pl.images?.[0]?.url}">
      <img src="${pl.images?.[0]?.url ?? 'https://via.placeholder.com/60'}" />
      <p>${pl.name}</p>
    </div>
  `).join('');

  document.querySelectorAll('#modal-playlist-list .playlist').forEach(el => {
    el.addEventListener('click', () => {
      const id = el.getAttribute('data-id');

      if (modalSelected.includes(id)) {
        modalSelected = modalSelected.filter(x => x !== id);
        el.classList.remove('selected');
      } else if (modalSelected.length < 3) {
        modalSelected.push(id);
        el.classList.add('selected');
      }

      saveBtn.disabled = modalSelected.length !== 3;
    });
  });
});

closeBtn.addEventListener('click', () => {
  modal.style.display = 'none';
  modalSelected = [];
});

saveBtn.addEventListener('click', async () => {
  const selectedEls = modalSelected.map(id =>
    document.querySelector(`.playlist[data-id="${id}"]`)
  );

  const featured = selectedEls.map(el => ({
    id: el.getAttribute("data-id"),
    name: el.getAttribute("data-name"),
    image: el.getAttribute("data-img")
  }));

  await fetch(`/feature-playlists`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, featured })
  });

  // Update UI
  document.getElementById("featured-playlists").innerHTML = featured.map(pl => `
    <div class="playlist">
      <a href="https://open.spotify.com/playlist/${pl.id}" target="_blank">
        <img src="${pl.image}" />
        <p>${pl.name}</p>
      </a>
    </div>
  `).join('');

  modal.style.display = 'none';
  modalSelected = [];
});