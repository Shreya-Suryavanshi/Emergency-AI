(function () {
  const cfg = window.__FIREBASE_CONFIG__;
  const configured = cfg && cfg.apiKey && cfg.apiKey !== "REPLACE_ME";

  function noop() {}

  window.saveEmergencyChatToFirestore = async function () { return noop(); };
  window.saveEmergencyContactsToFirestore = async function () { return noop(); };
  window.loadEmergencyContactsFromFirestore = async function () { return null; };
  window.loadUserChatHistory = async function () { return []; };
  window.getFirebaseUser = function () { return null; };
  window.firebaseConfigured = configured;

  if (!configured || typeof firebase === "undefined") {
    return;
  }

  try {
    firebase.initializeApp(cfg);
  } catch (e) {
    if (e.code !== "app/duplicate-app") {
      console.warn("Firebase init:", e);
      return;
    }
  }

  const auth = firebase.auth();
  const db = firebase.firestore();

  window.getFirebaseUser = function () {
    return auth.currentUser;
  };

  window.saveEmergencyChatToFirestore = async function (entry) {
    const u = auth.currentUser;
    if (!u) return;
    const payload = {
      msg: entry.msg || "",
      category: entry.category || "",
      translated: entry.translated || "",
      locationText: entry.locationText || "",
      lat: entry.lat ?? "",
      lon: entry.lon ?? "",
      peopleCaught: entry.peopleCaught ?? "",
      peopleInjured: entry.peopleInjured ?? "",
      lang: entry.lang || "",
      responsePreview: (entry.responsePreview || "").slice(0, 500),
      createdAt: firebase.firestore.FieldValue.serverTimestamp()
    };
    await db.collection("users").doc(u.uid).collection("chats").add(payload);
  };

  window.saveEmergencyContactsToFirestore = async function (contacts) {
    const u = auth.currentUser;
    if (!u) return;
    await db.collection("users").doc(u.uid).set(
      {
        emergencyContacts: contacts,
        updatedAt: firebase.firestore.FieldValue.serverTimestamp()
      },
      { merge: true }
    );
  };

  window.loadEmergencyContactsFromFirestore = async function () {
    const u = auth.currentUser;
    if (!u) return null;
    const snap = await db.collection("users").doc(u.uid).get();
    return snap.exists ? snap.data() : null;
  };

  window.loadUserChatHistory = async function () {
    const u = auth.currentUser;
    if (!u) return [];
    const snap = await db.collection("users").doc(u.uid).collection("chats").limit(200).get();
    const out = [];
    snap.forEach((doc) => {
      const d = doc.data();
      let ts = "";
      if (d.createdAt && d.createdAt.toDate) {
        ts = d.createdAt.toDate().toISOString();
      }
      out.push({
        id: doc.id,
        msg: d.msg,
        type: d.category,
        translated: d.translated,
        locationText: d.locationText,
        location: [d.lat, d.lon],
        peopleCaught: d.peopleCaught,
        peopleInjured: d.peopleInjured,
        ts: ts
      });
    });
    out.sort((a, b) => (b.ts || "").localeCompare(a.ts || ""));
    return out;
  };
})();
