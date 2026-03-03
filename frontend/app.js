const apiBaseFromStorage = (localStorage.getItem("api_base") || "").trim();
const normalizedStorageBase = apiBaseFromStorage.replace(/\/+$/, "").replace(/\/app$/, "");
const API = normalizedStorageBase || window.location.origin;

const feed = document.getElementById("chatFeed");
const input = document.getElementById("chatInput");
const actionBtn = document.getElementById("actionBtn");
const plusBtn = document.getElementById("plusBtn");
const plusMenu = document.getElementById("plusMenu");
const imageInput = document.getElementById("imageInput");
const speakToggle = document.getElementById("speakToggle");
let speakReplies = true;
let listening = false;

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = SpeechRecognition ? new SpeechRecognition() : null;

if (recognition) {
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
}

async function get(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed`);
  return res.json();
}

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

function addBubble(text, who = "alpha") {
  const node = document.createElement("article");
  node.className = `bubble ${who}`;
  node.textContent = text;
  feed.appendChild(node);
  feed.scrollTop = feed.scrollHeight;
}

async function refreshStatus() {
  const el = document.getElementById("statusLine");
  if (!el) return;
  try {
    const data = await get("/health");
    el.textContent = data.ai_enabled
      ? "AI status: online"
      : "AI status: offline (set OPENAI_API_KEY in backend/.env and restart)";
    el.style.color = data.ai_enabled ? "#ffd7d9" : "#ffe9bf";
  } catch (err) {
    el.textContent = "AI status: backend unreachable";
    el.style.color = "#ffd1d1";
  }
}

function speak(text) {
  if (!speakReplies || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

function renderExplain(data) {
  const points = (data.key_points || []).map((x) => `- ${x}`).join("\n");
  const steps = (data.steps_to_understand || []).map((x, i) => `${i + 1}. ${x}`).join("\n");
  return `${data.summary}\n\nKey points:\n${points}\n\nSteps:\n${steps}`;
}

function autoGrow() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
}

async function sendChat() {
  const message = input.value.trim();
  if (!message) return;
  addBubble(message, "user");
  input.value = "";
  autoGrow();
  actionBtn.textContent = "...";
  try {
    const data = await post("/api/chat", { message });
    addBubble(data.reply, "alpha");
    speak(data.reply);
  } catch (err) {
    addBubble(err.message, "alpha");
  } finally {
    actionBtn.textContent = "Mic";
  }
}

async function analyzeImage(file) {
  if (!file) return;
  addBubble("Please explain this image simply.", "user");
  addBubble("Analyzing image...", "alpha");
  const busyNode = feed.lastElementChild;
  try {
    const form = new FormData();
    form.append("file", file);
    const data = await post("/api/explain-image", form, true);
    const rendered = renderExplain(data);
    busyNode.textContent = rendered;
    speak(data.summary || rendered);
  } catch (err) {
    busyNode.textContent = err.message;
  }
}

function startListening() {
  if (!recognition) {
    addBubble("Voice input is not supported in this browser.", "alpha");
    return;
  }
  listening = true;
  actionBtn.textContent = "Stop";
  recognition.start();
}

function stopListening() {
  if (!recognition) return;
  listening = false;
  actionBtn.textContent = "Mic";
  recognition.stop();
}

if (recognition) {
  recognition.addEventListener("result", (event) => {
    const text = event.results[0][0].transcript || "";
    input.value = text.trim();
    autoGrow();
    if (input.value) {
      sendChat();
    }
  });
  recognition.addEventListener("error", () => {
    listening = false;
    actionBtn.textContent = "Mic";
  });
  recognition.addEventListener("end", () => {
    if (listening) {
      listening = false;
      actionBtn.textContent = "Mic";
    }
  });
}

input.addEventListener("input", autoGrow);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendChat();
  }
});

actionBtn.addEventListener("click", () => {
  if (input.value.trim()) {
    sendChat();
    return;
  }
  if (listening) {
    stopListening();
  } else {
    startListening();
  }
});

plusBtn.addEventListener("click", () => {
  plusMenu.classList.toggle("hidden");
});

document.addEventListener("click", (event) => {
  if (!plusMenu.contains(event.target) && !plusBtn.contains(event.target)) {
    plusMenu.classList.add("hidden");
  }
});

imageInput.addEventListener("change", async () => {
  const file = imageInput.files?.[0];
  plusMenu.classList.add("hidden");
  await analyzeImage(file);
  imageInput.value = "";
});

speakToggle.addEventListener("click", () => {
  speakReplies = !speakReplies;
  speakToggle.textContent = `Voice Replies: ${speakReplies ? "On" : "Off"}`;
});

if ("serviceWorker" in navigator) {
  // Clear stale service workers that can return invalid/null fetch responses.
  navigator.serviceWorker.getRegistrations().then((regs) => {
    regs.forEach((reg) => reg.unregister());
  });
}

refreshStatus();
