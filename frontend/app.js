const API = localStorage.getItem("api_base") || window.location.origin;

async function post(path, body, isForm = false) {
  const options = {
    method: "POST",
    body: isForm ? body : JSON.stringify(body),
    headers: isForm ? undefined : { "Content-Type": "application/json" },
  };
  const res = await fetch(`${API}${path}`, options);
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || "Request failed");
  }
  return res.json();
}

async function get(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || "Request failed");
  }
  return res.json();
}

function lines(items) {
  return items.map((x, i) => `${i + 1}. ${x}`).join("\n");
}

function renderProfile(data) {
  const out = document.getElementById("learningOut");
  const p = data.profile || {};
  out.textContent = [
    `Source: ${data.source}`,
    `Events analyzed: ${data.events_analyzed}`,
    `Updated: ${data.updated_at || "n/a"}`,
    "",
    `Summary: ${p.persona_summary || "n/a"}`,
    "",
    "Top focus areas:",
    lines(p.top_focus_areas || []),
    "",
    "Friction points:",
    lines(p.friction_points || []),
    "",
    "Active goals:",
    lines(p.active_goals || []),
    "",
    "Suggested routines:",
    lines(p.suggested_routines || []),
  ].join("\n");
}

async function loadLearningProfile() {
  const out = document.getElementById("learningOut");
  out.textContent = "Loading profile...";
  try {
    const data = await get("/api/learning/profile");
    renderProfile(data);
  } catch (err) {
    out.textContent = err.message;
  }
}

document.getElementById("refreshLearningBtn").addEventListener("click", async () => {
  const out = document.getElementById("learningOut");
  out.textContent = "Refreshing profile (AI)...";
  try {
    const data = await post("/api/learning/refresh", { use_ai: true });
    renderProfile(data);
  } catch (err) {
    out.textContent = err.message;
  }
});

document.getElementById("explainBtn").addEventListener("click", async () => {
  const content = document.getElementById("explainInput").value.trim();
  const out = document.getElementById("explainOut");
  if (!content) return;
  out.textContent = "Thinking...";
  try {
    const data = await post("/api/explain", { content, reading_level: "middle_school" });
    out.textContent = `Summary:\n${data.summary}\n\nKey points:\n${lines(data.key_points)}\n\nSteps:\n${lines(data.steps_to_understand)}`;
    loadLearningProfile();
  } catch (err) {
    out.textContent = err.message;
  }
});

document.getElementById("imageBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("imageInput");
  const out = document.getElementById("imageOut");
  const file = fileInput.files?.[0];
  if (!file) return;
  out.textContent = "Analyzing image...";
  try {
    const form = new FormData();
    form.append("file", file);
    const data = await post("/api/explain-image", form, true);
    out.textContent = `Summary:\n${data.summary}\n\nKey points:\n${lines(data.key_points)}\n\nSteps:\n${lines(data.steps_to_understand)}`;
    loadLearningProfile();
  } catch (err) {
    out.textContent = err.message;
  }
});

document.getElementById("chatBtn").addEventListener("click", async () => {
  const message = document.getElementById("chatInput").value.trim();
  const out = document.getElementById("chatOut");
  if (!message) return;
  out.textContent = "Thinking...";
  try {
    const data = await post("/api/chat", { message });
    out.textContent = data.reply;
    loadLearningProfile();
  } catch (err) {
    out.textContent = err.message;
  }
});

document.getElementById("checkinBtn").addEventListener("click", async () => {
  const stress = Number(document.getElementById("stress").value);
  const focus = Number(document.getElementById("focus").value);
  const notes = document.getElementById("checkinNotes").value;
  const out = document.getElementById("checkinOut");

  out.textContent = "Building your plan...";
  try {
    const data = await post("/api/checkin", { stress_level: stress, focus_level: focus, notes });
    out.textContent = `Coaching:\n${data.coaching}\n\nNext Action:\n${data.next_action}`;
    loadLearningProfile();
  } catch (err) {
    out.textContent = err.message;
  }
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/app/sw.js").catch(() => {});
}

loadLearningProfile();
