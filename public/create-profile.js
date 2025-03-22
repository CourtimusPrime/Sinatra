const urlParams = new URLSearchParams(window.location.search);
const username = urlParams.get("username");

let selected = [];

async function getPlaylists() {
  const res = await fetch(`/playlists?username=${username}`);
  const playlists = await res.json();

  const container = document.getElementById("playlist-list");
  container.innerHTML = playlists.map(pl => `
    <div class="playlist" data-id="${pl.id}" data-name="${pl.name}" data-img="${pl.images?.[0]?.url}">
      <img src="${pl.images?.[0]?.url ?? 'https://via.placeholder.com/60'}" />
      <p>${pl.name}</p>
    </div>
  `).join("");

  document.querySelectorAll(".playlist").forEach(el => {
    el.addEventListener("click", () => {
      const id = el.getAttribute("data-id");

      if (selected.includes(id)) {
        selected = selected.filter(x => x !== id);
        el.classList.remove("selected");
      } else if (selected.length < 3) {
        selected.push(id);
        el.classList.add("selected");
      }

      document.getElementById("submit-btn").disabled = selected.length !== 3;
    });
  });
}

document.getElementById("submit-btn").addEventListener("click", async () => {
  const selectedEls = selected.map(id =>
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

  window.location.href = `/home?username=${encodeURIComponent(username)}`;
});

getPlaylists();