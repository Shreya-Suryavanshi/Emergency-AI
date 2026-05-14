(async function () {
  try {
    const res = await fetch("/auth/me", { credentials: "same-origin" });
    const data = await res.json();
    if (!data || !data.authenticated) {
      const next = encodeURIComponent(window.location.pathname.split("/").pop() || "index.html");
      window.location.href = "login.html?next=" + next;
    }
  } catch (_e) {
    const next = encodeURIComponent(window.location.pathname.split("/").pop() || "index.html");
    window.location.href = "login.html?next=" + next;
  }
})();

