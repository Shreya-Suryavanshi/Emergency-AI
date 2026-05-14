let lat = "";
let lon = "";

// Get location
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            lat = pos.coords.latitude;
            lon = pos.coords.longitude;
        },
        () => {
            lat = "";
            lon = "";
        },
        { enableHighAccuracy: true, timeout: 8000 }
    );
}

function getUiLangCode() {
    const raw = document.getElementById("language")?.value || "en-IN";
    return (raw.split("-")[0] || "en").toLowerCase(); // "en" | "hi" | "mr"
}

// Quick emergency type buttons (your list + extra options)
const QUICK_TYPES = [
    { id: "house_fire", emoji: "🔥", enLabel: "House fire", enMessage: "House fire" },
    { id: "gas_explosion", emoji: "🔥", enLabel: "Gas explosion", enMessage: "Gas explosion" },
    { id: "forest_fire", emoji: "🔥", enLabel: "Forest fire", enMessage: "Forest fire" },
    { id: "electrical_fire", emoji: "🔥", enLabel: "Electrical fire", enMessage: "Electrical fire" },

    { id: "heart_attack", emoji: "🚑", enLabel: "Heart attack", enMessage: "Heart attack" },
    { id: "road_accident_injury", emoji: "🚑", enLabel: "Road accident injury", enMessage: "Road accident injury" },
    { id: "unconscious_person", emoji: "🚑", enLabel: "Unconscious person", enMessage: "Unconscious person" },
    { id: "severe_bleeding", emoji: "🚑", enLabel: "Severe bleeding", enMessage: "Severe bleeding" },

    { id: "theft_robbery", emoji: "🚓", enLabel: "Theft / robbery", enMessage: "Theft / robbery" },
    { id: "physical_assault", emoji: "🚓", enLabel: "Physical assault", enMessage: "Physical assault" },
    { id: "domestic_violence", emoji: "🚓", enLabel: "Domestic violence", enMessage: "Domestic violence" },
    { id: "kidnapping", emoji: "🚓", enLabel: "Kidnapping", enMessage: "Kidnapping" },

    { id: "flood", emoji: "🌊", enLabel: "Flood", enMessage: "Flood" },
    { id: "earthquake", emoji: "🌊", enLabel: "Earthquake", enMessage: "Earthquake" },
    { id: "cyclone_storm", emoji: "🌊", enLabel: "Cyclone / storm", enMessage: "Cyclone / storm" },
    { id: "landslide", emoji: "🌊", enLabel: "Landslide", enMessage: "Landslide" },

    { id: "electric_shock", emoji: "⚡", enLabel: "Electric shock", enMessage: "Electric shock" },
    { id: "gas_leakage", emoji: "⚡", enLabel: "Gas leakage", enMessage: "Gas leakage" },
    { id: "power_failure", emoji: "⚡", enLabel: "Power failure", enMessage: "Power failure" },
    { id: "water_pipeline_burst", emoji: "⚡", enLabel: "Water pipeline burst", enMessage: "Water pipeline burst" },

    // Extra helpful options
    { id: "building_collapse", emoji: "🚨", enLabel: "Building collapse", enMessage: "Building collapse" },
    { id: "fire_people_trapped", emoji: "🚨", enLabel: "Fire + people trapped", enMessage: "There is a fire and people are trapped" },
    { id: "accident_multiple_injured", emoji: "🚨", enLabel: "Accident with injuries", enMessage: "Accident happened and multiple people are injured" },
    { id: "suspicious_intruder", emoji: "🚨", enLabel: "Suspicious intruder", enMessage: "Suspicious intruder in house" }
];

// Basic UI translations for chips (label + message)
const QUICK_TYPES_I18N = {
    hi: {
        house_fire: { label: "घर में आग", message: "घर में आग लग गई है" },
        gas_explosion: { label: "गैस विस्फोट", message: "गैस का विस्फोट हुआ है" },
        forest_fire: { label: "जंगल में आग", message: "जंगल में आग लगी है" },
        electrical_fire: { label: "बिजली से आग", message: "शॉर्ट सर्किट से आग लगी है" },
        heart_attack: { label: "हार्ट अटैक", message: "हार्ट अटैक का मामला है" },
        road_accident_injury: { label: "सड़क दुर्घटना (चोट)", message: "सड़क दुर्घटना में चोट लगी है" },
        unconscious_person: { label: "बेहोश व्यक्ति", message: "एक व्यक्ति बेहोश है" },
        severe_bleeding: { label: "ज्यादा खून बहना", message: "बहुत ज्यादा खून बह रहा है" },
        theft_robbery: { label: "चोरी / डकैती", message: "चोरी / डकैती हो रही है" },
        physical_assault: { label: "मारपीट", message: "किसी पर हमला / मारपीट हो रही है" },
        domestic_violence: { label: "घरेलू हिंसा", message: "घर में घरेलू हिंसा हो रही है" },
        kidnapping: { label: "अपहरण", message: "अपहरण का मामला है" },
        flood: { label: "बाढ़", message: "इलाके में बाढ़ आ गई है" },
        earthquake: { label: "भूकंप", message: "भूकंप आया है" },
        cyclone_storm: { label: "चक्रवात / तूफान", message: "तेज तूफान / चक्रवात है" },
        landslide: { label: "भूस्खलन", message: "भूस्खलन हो रहा है" },
        electric_shock: { label: "बिजली का झटका", message: "किसी को बिजली का झटका लगा है" },
        gas_leakage: { label: "गैस रिसाव", message: "गैस लीक हो रही है" },
        power_failure: { label: "बिजली गुल", message: "इलाके में बिजली गुल है" },
        water_pipeline_burst: { label: "पानी की पाइप फट गई", message: "पानी की पाइपलाइन फट गई है" },
        building_collapse: { label: "इमारत गिरना", message: "इमारत गिर गई है" },
        fire_people_trapped: { label: "आग + लोग फंसे", message: "आग लगी है और लोग फंसे हुए हैं" },
        accident_multiple_injured: { label: "दुर्घटना (कई घायल)", message: "दुर्घटना हुई है और कई लोग घायल हैं" },
        suspicious_intruder: { label: "संदिग्ध घुसपैठिया", message: "घर में संदिग्ध घुसपैठिया है" }
    },
    mr: {
        house_fire: { label: "घराला आग", message: "घराला आग लागली आहे" },
        gas_explosion: { label: "गॅस स्फोट", message: "गॅसचा स्फोट झाला आहे" },
        forest_fire: { label: "जंगलात आग", message: "जंगलात आग लागली आहे" },
        electrical_fire: { label: "विद्युत आग", message: "शॉर्ट सर्किटमुळे आग लागली आहे" },
        heart_attack: { label: "हार्ट अटॅक", message: "हार्ट अटॅकचा केस आहे" },
        road_accident_injury: { label: "रस्ते अपघात (इजा)", message: "रस्ते अपघातात इजा झाली आहे" },
        unconscious_person: { label: "बेशुद्ध व्यक्ती", message: "एक व्यक्ती बेशुद्ध आहे" },
        severe_bleeding: { label: "जास्त रक्तस्राव", message: "खूप जास्त रक्तस्राव होत आहे" },
        theft_robbery: { label: "चोरी / दरोडा", message: "चोरी / दरोडा चालू आहे" },
        physical_assault: { label: "मारहाण", message: "कुणावर तरी हल्ला / मारहाण होत आहे" },
        domestic_violence: { label: "घरगुती हिंसा", message: "घरात घरगुती हिंसा होत आहे" },
        kidnapping: { label: "अपहरण", message: "अपहरणाचा प्रकार आहे" },
        flood: { label: "पूर", message: "परिसरात पूर आला आहे" },
        earthquake: { label: "भूकंप", message: "भूकंप झाला आहे" },
        cyclone_storm: { label: "चक्रीवादळ / वादळ", message: "तीव्र वादळ / चक्रीवादळ आहे" },
        landslide: { label: "भूस्खलन", message: "भूस्खलन झाले आहे" },
        electric_shock: { label: "विद्युत धक्का", message: "कुणाला तरी विजेचा धक्का लागला आहे" },
        gas_leakage: { label: "गॅस गळती", message: "गॅस लीक होत आहे" },
        power_failure: { label: "वीज बंद", message: "परिसरात वीज बंद आहे" },
        water_pipeline_burst: { label: "पाण्याची पाइप फुटली", message: "पाण्याची पाइपलाइन फुटली आहे" },
        building_collapse: { label: "इमारत कोसळली", message: "इमारत कोसळली आहे" },
        fire_people_trapped: { label: "आग + लोक अडकले", message: "आग लागली आहे आणि लोक अडकले आहेत" },
        accident_multiple_injured: { label: "अपघात (अनेक जखमी)", message: "अपघात झाला आहे आणि अनेक लोक जखमी आहेत" },
        suspicious_intruder: { label: "संशयास्पद घुसखोर", message: "घरात संशयास्पद घुसखोर आहे" }
    }
};

function renderQuickTypes() {
    const host = document.getElementById("quick-types");
    if (!host) return;
    const lang = getUiLangCode();
    host.innerHTML = QUICK_TYPES.map((t) => {
        const tr = QUICK_TYPES_I18N[lang]?.[t.id];
        const label = `${t.emoji} ${tr?.label || t.enLabel}`;
        const message = tr?.message || t.enMessage;
        return `<div class="chip" data-msg="${escapeHtml(message)}">${escapeHtml(label)}</div>`;
    }).join("");
}

function initQuickTypes() {
    const host = document.getElementById("quick-types");
    if (!host) return;

    renderQuickTypes();

    host.addEventListener("click", (e) => {
        const chip = e.target && e.target.closest ? e.target.closest(".chip") : null;
        if (!chip) return;
        const msg = chip.getAttribute("data-msg") || "";
        const input = document.getElementById("msg");
        if (input) {
            input.value = msg;
            input.focus();
        }
    });

    const langSelect = document.getElementById("language");
    if (langSelect) {
        langSelect.addEventListener("change", () => {
            renderQuickTypes();
        });
    }
}

// Send message
async function sendMessage() {
    let msg = document.getElementById("msg").value;
    if (!msg || !msg.trim()) return;

    const locationText = (document.getElementById("locationText")?.value || "").trim();
    const peopleCaughtRaw = (document.getElementById("peopleCaught")?.value || "").trim();
    const peopleInjuredRaw = (document.getElementById("peopleInjured")?.value || "").trim();
    const peopleCaught = peopleCaughtRaw === "" ? "" : Number(peopleCaughtRaw);
    const peopleInjured = peopleInjuredRaw === "" ? "" : Number(peopleInjuredRaw);
    const lang = (document.getElementById("language")?.value || "en-IN");

    let res = await fetch("/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            message: msg.trim(),
            lat: lat,
            lon: lon,
            locationText: locationText,
            peopleCaught: Number.isFinite(peopleCaught) ? peopleCaught : "",
            peopleInjured: Number.isFinite(peopleInjured) ? peopleInjured : "",
            lang: lang
        })
    });

    let data = await res.json();

    try {
        if (typeof window.saveEmergencyChatToFirestore === "function") {
            await window.saveEmergencyChatToFirestore({
                msg: msg.trim(),
                category: data.category,
                translated: data.translated,
                locationText,
                lat,
                lon,
                peopleCaught: Number.isFinite(peopleCaught) ? peopleCaught : "",
                peopleInjured: Number.isFinite(peopleInjured) ? peopleInjured : "",
                lang,
                responsePreview: data.response
            });
        }
    } catch (e) {
        /* optional cloud save */
    }

    let box = document.getElementById("chat-box");

    const details = [];
    if (locationText) details.push(`📍 ${locationText}`);
    if (Number.isFinite(peopleCaught)) details.push(`🧍 Trapped: ${peopleCaught}`);
    if (Number.isFinite(peopleInjured)) details.push(`🩹 Injured: ${peopleInjured}`);
    const detailsHtml = details.length ? `<div class="muted" style="margin-top:6px; font-size: 12px;">${escapeHtml(details.join(" • "))}</div>` : "";

    box.innerHTML += `<div class="msg msg-user"><div class="bubble"><div class="label">You</div>${escapeHtml(msg.trim())}${detailsHtml}</div></div>`;
    box.innerHTML += `<div class="msg msg-ai"><div class="bubble"><div class="label">AI</div>${escapeHtml(data.response || "")}</div></div>`;
    box.scrollTop = box.scrollHeight;
    document.getElementById("msg").value = "";
}

function escapeHtml(str) {
    return String(str)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#039;");
}

function initServiceQuickButtons() {
    document.querySelectorAll("[data-service]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const svc = btn.getAttribute("data-service");
            const lang = getUiLangCode();
            const messages = {
                fire: {
                    en: "House fire emergency",
                    hi: "घर में आग लग गई है",
                    mr: "घराला आग लागली आहे"
                },
                medical: {
                    en: "Medical emergency need ambulance",
                    hi: "चिकित्सा आपातकालीन एम्बुलेंस चाहिए",
                    mr: "वैद्यकीय आपत्कालीन रुग्णवाहिका हवी आहे"
                },
                police: {
                    en: "Police emergency crime in progress",
                    hi: "पुलिस आपातकाल अपराध हो रहा है",
                    mr: "पोलिस आपत्कालीन गुन्हा सुरू आहे"
                }
            };
            const pack = messages[svc];
            const text = pack ? (pack[lang] || pack.en) : "";
            const input = document.getElementById("msg");
            if (input && text) {
                input.value = text;
                input.focus();
            }
        });
    });
}

// Init
initQuickTypes();
initServiceQuickButtons();

// Voice input
function startVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Speech recognition not supported in this browser.");
        return;
    }
    let recognition = new SpeechRecognition();
    const langSelect = document.getElementById("language");
    recognition.lang = (langSelect && langSelect.value) ? langSelect.value : "en-IN";

    recognition.onresult = function(event) {
        document.getElementById("msg").value =
            event.results[0][0].transcript;
    };

    recognition.start();
}