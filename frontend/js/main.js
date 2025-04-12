// frontend/js/main.js

// Global auth check
(async () => {
    const userId = localStorage.getItem("user_id");
    const path = window.location.pathname;
  
    const publicPages = ["/", "/index.html", "/login-page", "/login.html"];
  
    if (!userId && !publicPages.includes(path)) {
      // If not signed in and trying to access restricted page
      window.location.href = "/login-page";
      return;
    }
  
    if (userId) {
      // Optional: confirm if user exists or is valid
      try {
        const res = await fetch(`/me?user_id=${userId}`);
        if (!res.ok) throw new Error();
      } catch (err) {
        localStorage.removeItem("user_id");
        window.location.href = "/login-page";
        return;
      }
  
      // Check onboarding status
      const res = await fetch(`/has-completed-onboarding?user_id=${userId}`);
      const { completed } = await res.json();
  
      if (completed && path === "/onboard") {
        window.location.href = "/home";
      }
  
      if (!completed && path !== "/onboard") {
        window.location.href = `/onboard?user_id=${userId}`;
      }
    }
  })();