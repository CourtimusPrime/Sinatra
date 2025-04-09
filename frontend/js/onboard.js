// frontend/js/onboard.js

let userId = new URLSearchParams(window.location.search).get("user_id");
localStorage.setItem("user_id", userId);

let currentStep = 0;
const steps = document.querySelectorAll(".step");

let userData = {
  user_id: userId,
  playlist_ids: [],
  display_name: "",
  profile_picture: ""
};

const nextBtn = document.getElementById("next-button");
nextBtn.disabled = true;

async function fetchUserData() {
  const res = await fetch(`/me?user_id=${userId}`);
  const user = await res.json();

  document.getElementById("current-name").textContent = `"${user.display_name}"`;
  document.getElementById("profile-pic").src = user.profile_picture;
  userData.display_name = user.display_name;
  userData.profile_picture = user.profile_picture;

  const playlists = await fetch(`/playlists?user_id=${userId}`).then(r => r.json());
  const list = document.getElementById("playlist-list");

  let filteredPlaylists = playlists.items;

  function renderPlaylists(list) {
    const listContainer = document.getElementById("playlist-list");
    listContainer.innerHTML = "";
  
    list.forEach(p => {
      const div = document.createElement("label");
      div.className = "playlist-card";
  
      div.innerHTML = `
        <input type="checkbox" value="${p.id}">
        <img src="${p.image || '/static/default-cover.jpg'}" class="playlist-cover" />
        <div class="playlist-text">
          <p class="playlist-name">${p.name}</p>
          <p class="playlist-count">${p.tracks} ${p.tracks === 1 ? "song" : "songs"}</p>
        </div>
      `;
  
      // Toggle checked class
      div.addEventListener("click", (e) => {
        if (e.target.tagName !== "INPUT") {
          const checkbox = div.querySelector("input");
          checkbox.checked = !checkbox.checked;
        }
  
        div.classList.toggle("checked", div.querySelector("input").checked);
        updateSelectedCount();
      });
  
      listContainer.appendChild(div);
    });
  
    // 👇 Move this inside here so listContainer is available
    listContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      cb.addEventListener("change", updateSelectedCount);
    });
  
    updateSelectedCount(); // also update count after rendering
  }

function updateNextButtonState() {
    const checked = document.querySelectorAll("#playlist-list input:checked");
    nextBtn.disabled = checked.length === 0;
  }

renderPlaylists(filteredPlaylists);
listContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => {
  cb.addEventListener("change", updateSelectedCount);
});

function updateSelectedCount() {
  const count = document.querySelectorAll("#playlist-list input:checked").length;
  document.getElementById("selected-count").textContent = `${count} playlist${count === 1 ? "" : "s"} selected`;
  document.getElementById("next-button").disabled = count === 0;
}

// Search Filter
document.getElementById("search-bar").addEventListener("input", e => {
  const q = e.target.value.toLowerCase();
  const filtered = playlists.items.filter(p =>
    p.name.toLowerCase().includes(q)
  );
  filteredPlaylists = filtered;
  renderPlaylists(filtered);
  listContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener("change", updateSelectedCount);
  });
});

// Sorting
document.getElementById("sort-select").addEventListener("change", e => {
  const val = e.target.value;
  const sorted = [...filteredPlaylists];

  if (val === "songs-desc") sorted.sort((a, b) => b.tracks - a.tracks);
  if (val === "songs-asc") sorted.sort((a, b) => a.tracks - b.tracks);
  if (val === "name-asc") sorted.sort((a, b) => a.name.localeCompare(b.name));
  if (val === "name-desc") sorted.sort((a, b) => b.name.localeCompare(a.name));

  renderPlaylists(sorted);
});
}

function nextStep() {
  // Step 1: Validate playlist selection
  if (currentStep === 0) {
    const checked = document.querySelectorAll("#playlist-list input:checked");
    if (checked.length === 0) {
      alert("Please select at least one playlist.");
      return;
    }
    userData.playlist_ids = Array.from(checked).map(cb => cb.value);
  }

  // Step 2: Validate name change (if needed)
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
  }

  // Step 3: Validate image (if user uploaded one)
  if (currentStep === 2) {
    const upload = document.getElementById("profile-upload").files[0];
    if (upload) {
      const reader = new FileReader();
      reader.onloadend = () => {
        userData.profile_picture = reader.result;
        advance();
      };
      reader.readAsDataURL(upload);
      return;
    }
  }

  // Step 4: Final submission handler
  if (currentStep === 3) {
    fetch("/complete-onboarding", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData)
    })
      .then(res => {
        if (!res.ok) throw new Error("Failed to complete onboarding");
        return res.json();
      })
      .then(() => {
        setTimeout(() => {
          window.location.href = "/home";
        }, 1000);
      })
      .catch(err => {
        console.error("🚨 Onboarding error:", err);
        alert("Something went wrong while saving your profile. Please try again.");
        nextBtn.disabled = false; // Re-enable the button on error
      });
  }

  advance();
}

function advance() {
  steps[currentStep].classList.remove("active");
  currentStep += 1;
  if (currentStep < steps.length) {
    steps[currentStep].classList.add("active");
  }
}

// Extra UI logic
document.querySelectorAll('input[name="nameOption"]').forEach(opt => {
  opt.addEventListener("change", () => {
    const box = document.getElementById("name-change-box");
    box.style.display = opt.value === "change" ? "block" : "none";
  });
});

window.onload = () => {
  fetchUserData(); // Fetch user data
  steps[currentStep].classList.add("active"); // Initialize the first step as active
};