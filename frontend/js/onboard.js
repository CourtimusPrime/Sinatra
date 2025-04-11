// frontend/js/onboard.js

let userId = new URLSearchParams(window.location.search).get("user_id");
localStorage.setItem("user_id", userId);

let currentStep = 0;
const steps = document.querySelectorAll(".step");

let userData = {
  user_id: userId,
  playlist_ids: [],
  display_name: "",
  profile_picture: "",
  featured_playlists: []
};

const fallback_picture = "https://media.tenor.com/6BUVtTultLsAAAAM/crash.gif"

const nextBtn = document.getElementById("next-button");
const listContainer = document.getElementById("playlist-list");
nextBtn.disabled = true;

function loadSavedSelections() {
  const saved = localStorage.getItem("selected_playlists");
  if (saved) {
    userData.playlist_ids = JSON.parse(saved);
    console.log("🔁 Restored playlist_ids from localStorage:", userData.playlist_ids);
  }
}

async function fetchUserData() {
  const res = await fetch(`/me?user_id=${userId}`);
  const user = await res.json();

  document.getElementById("current-name").textContent = `"${user.display_name}"`;
  document.getElementById("profile-pic").src = user.profile_picture || fallback_picture;
  console.log("🖼 profile_picture:", user.profile_picture);
  userData.display_name = user.display_name;
  userData.profile_picture = user.profile_picture || fallback_picture;

  const playlistsRes = await fetch(`/playlists?user_id=${userId}`);
  const playlistsData = await playlistsRes.json();

  let allPlaylists = playlistsData.items.filter(
    p => typeof p.tracks === "number" && p.tracks >= 5
  );
  let filteredPlaylists = [...allPlaylists];

  renderPlaylists(filteredPlaylists);

  document.getElementById("search-bar").addEventListener("input", e => {
    const q = e.target.value.toLowerCase();
    filteredPlaylists = allPlaylists.filter(p =>
      p.name.toLowerCase().includes(q)
    );
    renderPlaylists(filteredPlaylists);
  });

  document.getElementById("sort-select").addEventListener("change", e => {
    const val = e.target.value;
    const sorted = [...filteredPlaylists];

    if (val === "songs-desc") sorted.sort((a, b) => b.tracks - a.tracks);
    else if (val === "songs-asc") sorted.sort((a, b) => a.tracks - b.tracks);
    else if (val === "name-asc") sorted.sort((a, b) => a.name.localeCompare(b.name));
    else if (val === "name-desc") sorted.sort((a, b) => b.name.localeCompare(a.name));

    renderPlaylists(sorted);
  });

  document.getElementById("toggle-select-all").addEventListener("click", () => {
    const allVisible = listContainer.querySelectorAll('input[type="checkbox"]');
    const isAllSelected = Array.from(allVisible).every(cb => cb.checked);

    allVisible.forEach(cb => {
      cb.checked = !isAllSelected;
      const card = cb.closest(".playlist-card");
      handleSelectionChange(cb.value, cb.checked, card);
    });

    document.getElementById("toggle-select-all").textContent = isAllSelected ? "Select All" : "Deselect All";
  });
}

function renderPlaylists(list) {
  const selectedIds = new Set(userData.playlist_ids);
  listContainer.innerHTML = "";
  list.forEach(p => {
    const div = document.createElement("div");
    div.className = "playlist-card";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = p.id;
    checkbox.id = `checkbox-${p.id}`;
    if (selectedIds.has(p.id)) {
      checkbox.checked = true;
      div.classList.add("checked");
    }

    const image = document.createElement("img");
    image.src = p.image || "/static/default-cover.jpg";
    image.className = "playlist-cover";

    const textContainer = document.createElement("div");
    textContainer.className = "playlist-text";
    textContainer.innerHTML = `
      <p class="playlist-name">${p.name}</p>
      <p class="playlist-count">${p.tracks} ${p.tracks === 1 ? "song" : "songs"}</p>
    `;

    checkbox.addEventListener("click", e => {
      e.stopPropagation();
      handleSelectionChange(p.id, checkbox.checked, div);
    });

    div.addEventListener("click", () => {
      checkbox.checked = !checkbox.checked;
      handleSelectionChange(p.id, checkbox.checked, div);
    });

    div.appendChild(checkbox);
    div.appendChild(image);
    div.appendChild(textContainer);
    listContainer.appendChild(div);
  });

  updateSelectedCount();
}

function handleSelectionChange(id, isChecked, cardEl) {
  cardEl.classList.toggle("checked", isChecked);

  if (isChecked && !userData.playlist_ids.includes(id)) {
    userData.playlist_ids.push(id);
  } else if (!isChecked) {
    userData.playlist_ids = userData.playlist_ids.filter(pid => pid !== id);
  }

  localStorage.setItem("selected_playlists", JSON.stringify(userData.playlist_ids));
  updateSelectedCount();
}

function updateSelectedCount() {
  const count = userData.playlist_ids.length;
  document.getElementById("selected-count").textContent =
    `${count} playlist${count === 1 ? "" : "s"} selected`;
  nextBtn.disabled = count === 0;
}

function nextStep() {
  if (currentStep === 0) {
    const checked = document.querySelectorAll("#playlist-list input:checked");
    userData.playlist_ids = Array.from(checked).map(cb => cb.value);
    if (userData.playlist_ids.length === 0) {
      alert("Please select at least one playlist.");
      return;
    }
  
    prepareFeaturedStep();
    advance(); // Goes to step-1-featured
    return;
  }
  
  if (currentStep === 1) {
    if (userData.featured_playlists.length !== 3) {
      alert("Please select exactly 3 featured playlists.");
      return;
    }
    advance(); // goes to name step
    return;
  }

  if (currentStep === 1) {
    const choice = document.querySelector('input[name="nameOption"]:checked').value;
    if (choice === "change") {
      const newName = document.getElementById("new-name").value.trim();
      if (!newName) {
        alert("Please enter your name.");
        return;
      }
      userData.display_name = newName;
    }
    advance();
    return;
  }

  if (currentStep === 2) {
    const upload = document.getElementById("profile-upload").files[0];
    if (upload) {
      const reader = new FileReader();
      reader.onloadend = () => {
        userData.profile_picture = reader.result;
        advance(); // ✅ go to step 3, then it’ll trigger logic below
        maybeSubmitOnboarding(); // ✅ handle submission from step 3
      };
      reader.readAsDataURL(upload);
      return;
    }

    advance(); // no upload? just move on
    maybeSubmitOnboarding();
    return;
  }

  if (currentStep === 3) {
    maybeSubmitOnboarding();
  }
}

function advance() {
  console.log("➡️ Moving from step", currentStep);
  steps[currentStep].classList.remove("active");
  currentStep += 1;
  console.log(`🟢 Now on step ${currentStep}`);

  if (currentStep < steps.length) {
    steps[currentStep].classList.add("active");
  }

  // Show footer only on step 0 (playlist selection)
  const footer = document.getElementById("onboarding-footer");
  footer.style.display = currentStep === 0 ? "flex" : "none";
}

function maybeSubmitOnboarding() {
  if (currentStep !== 3) return;

  if (!userData.profile_picture) {
    userData.profile_picture = "https://www.rollingstone.com/wp-content/uploads/2020/11/alex-trebek-obit.jpg?w=1600&h=900&crop=1"; // <-- 💥 This fixes the crash
  }

  console.log("📤 Submitting final onboarding data:", userData);

  fetch("/complete-onboarding", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...userData,
      featured_playlists: userData.featured_playlists
    })
  })
    .then(res => {
      if (!res.ok) throw new Error("Failed to complete onboarding");
      return res.json();
    })
    .then(() => {
      console.log("✅ Onboarding complete, redirecting to /home");
      setTimeout(() => {
        window.location.href = "/home";
      }, 1000);
    })
    .catch(err => {
      console.error("🚨 Onboarding error:", err);
      alert("Something went wrong while saving your profile. Please try again.");
      nextBtn.disabled = false;
    });
}

function prepareFeaturedStep() {
  const container = document.getElementById("featured-playlist-list");
  container.innerHTML = "";
  userData.featured_playlists = [];

  const selected = userData.playlist_ids;
  document.getElementById("total-selected-count").textContent = selected.length;

  selected.forEach(pid => {
    const origCard = document.getElementById(`checkbox-${pid}`).closest(".playlist-card");
    const clone = origCard.cloneNode(true);
    const checkbox = clone.querySelector("input[type='checkbox']");
    checkbox.checked = false;

    checkbox.addEventListener("click", e => {
      e.stopPropagation();
      handleFeaturedSelection(pid, checkbox.checked, clone);
    });

    clone.addEventListener("click", () => {
      checkbox.checked = !checkbox.checked;
      handleFeaturedSelection(pid, checkbox.checked, clone);
    });

    container.appendChild(clone);
  });
}

function handleFeaturedSelection(id, isChecked, cardEl) {
  if (isChecked && userData.featured_playlists.length >= 3) {
    alert("Only 3 featured playlists allowed.");
    cardEl.querySelector("input").checked = false;
    return;
  }

  cardEl.classList.toggle("checked", isChecked);

  if (isChecked) {
    userData.featured_playlists.push(id);
  } else {
    userData.featured_playlists = userData.featured_playlists.filter(pid => pid !== id);
  }

  const count = userData.featured_playlists.length;
  document.getElementById("featured-count").textContent = `${count} of 3 selected`;
  document.getElementById("featured-next-button").disabled = count !== 3;
}

document.querySelectorAll('input[name="nameOption"]').forEach(opt => {
  opt.addEventListener("change", () => {
    const box = document.getElementById("name-change-box");
    box.style.display = opt.value === "change" ? "block" : "none";
  });
});

window.onload = () => {
  console.log("🚀 Onboarding page loaded for user:", userId);
  loadSavedSelections();
  fetchUserData();
  steps[currentStep].classList.add("active");
  document.getElementById("onboarding-footer").style.display = currentStep === 0 ? "flex" : "none";
};