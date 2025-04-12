// frontend/js/main.js

// 🔐 Store user_id from URL if it's present
const urlParams = new URLSearchParams(window.location.search);
const userIdFromUrl = urlParams.get("user_id");
if (userIdFromUrl) {
  console.log("🆔 Found user_id in URL, storing in localStorage:", userIdFromUrl);
  localStorage.setItem("user_id", userIdFromUrl);
}

// 🌍 Global auth check
(async () => {
  const userId = localStorage.getItem("user_id");
  const path = window.location.pathname;
  const publicPages = ["/", "/index.html", "/login-page", "/login.html"];

  if (!userId && !publicPages.includes(path)) {
    console.warn("🚫 No user_id found, redirecting to /login-page");
    window.location.href = "/login-page";
    return;
  }

  if (userId) {
    try {
      const res = await fetch(`/me?user_id=${userId}`);
      if (!res.ok) throw new Error("Invalid user or expired token");
    } catch (err) {
      console.error("❌ Auth check failed, clearing user_id");
      localStorage.removeItem("user_id");
      window.location.href = "/login-page";
      return;
    }

    // 🎓 Onboarding logic
    const res = await fetch(`/has-completed-onboarding?user_id=${userId}`);
    const { completed } = await res.json();

    if (completed && path === "/onboard") {
      console.log("✅ Already onboarded, sending to /home");
      window.location.href = "/home";
    }

    if (!completed && path !== "/onboard") {
      console.log("🧭 Needs onboarding, redirecting...");
      window.location.href = `/onboard?user_id=${userId}`;
    }
  }
})();