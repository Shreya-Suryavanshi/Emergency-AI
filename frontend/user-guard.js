(async function () {
  try {
    const res = await fetch("/auth/me", { credentials: "same-origin" });
    const data = await res.json();
    if (!data || !data.authenticated) {
      const next = encodeURIComponent(window.location.pathname.split("/").pop() || "user.html");
      window.location.href = "login.html?next=" + next;
      return;
    }
    if (data.user && data.user.role === "admin") {
      window.location.href = "admin.html";
    }
  } catch (_e) {
    const next = encodeURIComponent(window.location.pathname.split("/").pop() || "user.html");
    window.location.href = "login.html?next=" + next;
  }
})();

