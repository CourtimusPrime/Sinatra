// frontend/js/home.js
const userId = localStorage.getItem("user_id");
if (!userId) {
  window.location.href = "/";
}

async function loadUser() {
  const user = await fetch(`/me?user_id=${userId}`).then(r => r.json());

  document.getElementById("user-name").textContent = user.display_name;
  document.getElementById("profile-pic").src = user.profile_picture;

  const featured = user.featured_playlists || [];
  const playlistContainer = document.getElementById("featured-playlists");
  playlistContainer.innerHTML = "";

  if (featured.length === 0) {
    playlistContainer.innerHTML = `<p>No featured playlists selected yet.</p>`;
  } else {
    for (const playlistId of featured) {
      const res = await fetch(`/playlist-info?user_id=${userId}&playlist_id=${playlistId}`);
      const data = await res.json();

      const div = document.createElement("div");
      div.className = "playlist-card";
      div.innerHTML = `
        <p><strong>${data.name}</strong></p>
        <img src="${data.image}" width="100" />
      `;
      playlistContainer.appendChild(div);
    }
  }

  // Add "See all" link
  const seeAll = document.createElement("a");
  seeAll.href = "/playlists";
  seeAll.textContent = "See all playlists →";
  seeAll.className = "see-all-link";
  playlistContainer.appendChild(seeAll);
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

async function loadSunburst() {
  try {
    const res = await fetch(`/genres?user_id=${userId}`);
    const data = await res.json();

    if (!data.sunburst) {
      console.error("Sunburst data is missing:", data);
      return;
    }

    document.getElementById("genre-summary").textContent = data.summary;

    const sunburst = data.sunburst;

    const labels = [];
    const parents = [];
    const values = [];
    const colors = [];

    function flatten(node, parentName = "", depth = 0) {
      if (node.name) {
        labels.push(node.name);
        parents.push(parentName);

        if (node.value !== undefined) {
          values.push(node.value);
        } else if (!node.children) {
          values.push(0);
        }

        // Use metaGenreColors for coloring
        const top = depth === 0 ? node.name : parentName;
        const colorKey = top.toLowerCase();
        colors.push(metaGenreColors[colorKey] || "#cccccc");
      }

      if (node.children) {
        for (const child of node.children) {
          flatten(child, node.name, depth + 1);
        }
      }
    }

    flatten(sunburst);

    const trace = {
      type: "sunburst",
      labels,
      parents,
      values,
      marker: { colors },
      branchvalues: "total",
      outsidetextfont: { size: 16, color: "#333" },
      leaf: { opacity: 0.6 },
      marker: { line: { width: 2 } }
    };

    const layout = {
      autosize: true,
      margin: { t: 0, r: 0, b: 0, l: 0 },
      sunburstcolorway: ["#636efa", "#ef553b", "#00cc96", "#ab63fa", "#19d3f3"],
      extendsunburstcolorway: true,
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)"
    };

    Plotly.newPlot("genre-sunburst", [trace], layout, {
      displayModeBar: false,
      responsive: true
    });
  } catch (error) {
    console.error("Failed to load sunburst chart:", error);
  }
}

// Call loadNowPlaying every 30 seconds
setInterval(loadNowPlaying, 30000);

window.onload = () => {
  loadUser();
  loadNowPlaying();
  loadSunburst();
};

const metaGenreColors = {
  rock: "#ff6f61",
  pop: "#6b5b95",
  rnb: "#88b04b",
  "r&b": "#88b04b",
  electronic: "#009688",
  hiphop: "#f7cac9",
  "hip-hop": "#f7cac9",
  metal: "#505050",
  other: "#9e9e9e"
};