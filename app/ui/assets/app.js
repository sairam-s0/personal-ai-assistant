const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#sendButton");
const clearButton = document.querySelector("#clearChat");
const newChatButton = document.querySelector("#newChat");
const sessionsList = document.querySelector("#sessions");
const notifyButton = document.querySelector("#notifyButton");
const localTime = document.querySelector("#localTime");
const calendarLogin = document.querySelector("#calendarLogin");
const calendarStatus = document.querySelector("#calendarStatus");
const calendarPhaseStatus = document.querySelector("#calendarPhaseStatus");
const statusLabel = document.querySelector("#connectionStatus");
const quickPrompts = document.querySelectorAll(".quick-prompt");

const history = [];
let sessionId = localStorage.getItem("assistant.sessionId") || null;

function setStatus(text) {
  if (statusLabel) {
    statusLabel.textContent = text;
  }
}

function scrollToLatest() {
  messages.scrollTop = messages.scrollHeight;
}

function autoSizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
}

function appendMessage(role, content, options = {}) {
  const article = document.createElement("article");
  article.className = `message ${role}${options.typing ? " typing" : ""}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const paragraph = document.createElement("p");
  paragraph.textContent = content;

  bubble.appendChild(paragraph);
  article.appendChild(bubble);
  messages.appendChild(article);
  scrollToLatest();
  return article;
}

function resetMessages() {
  history.splice(0, history.length);
  messages.innerHTML = "";
  appendMessage("assistant", "Ready. Tell me what you want to plan, write, or reason through.");
}

function formatDate(value) {
  if (!value) {
    return "";
  }
  return new Date(value.replace(" ", "T")).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function refreshTime() {
  if (!localTime) {
    return;
  }
  try {
    const response = await fetch("/time");
    const data = await response.json();
    localTime.textContent = `${data.weekday}, ${data.date} ${data.time} ${data.timezone}`;
  } catch {
    localTime.textContent = "Unavailable";
  }
}

async function refreshHealth() {
  try {
    const response = await fetch("/health");
    if (!response.ok) {
      throw new Error("health check failed");
    }
    const data = await response.json();
    setStatus(`Server ${data.status}`);
  } catch {
    setStatus("Server unavailable");
  }
}

async function refreshGoogleCalendarStatus() {
  if (!calendarStatus) {
    return;
  }
  try {
    const response = await fetch("/google-calendar/status");
    const data = await response.json();
    if (data.ok) {
      calendarStatus.textContent = "Connected";
      calendarStatus.classList.remove("muted");
      calendarLogin?.classList.add("hidden");
      if (calendarPhaseStatus) {
        calendarPhaseStatus.textContent = "Ready";
      }
      return;
    }

    if ((data.missing || []).some((path) => path.includes("credentials.json"))) {
      calendarStatus.textContent = "Add credentials.json first";
    } else {
      calendarStatus.textContent = "Login required";
    }
    calendarStatus.classList.add("muted");
    calendarLogin?.classList.remove("hidden");
    if (calendarPhaseStatus) {
      calendarPhaseStatus.textContent = "Login";
    }
  } catch {
    calendarStatus.textContent = "Calendar status unavailable";
    calendarStatus.classList.add("muted");
  }
}

async function requestNotificationPermission() {
  if (!("Notification" in window)) {
    appendMessage("assistant", "Browser notifications are not supported here.");
    return;
  }
  const result = await Notification.requestPermission();
  appendMessage("assistant", `Notification permission: ${result}.`);
}

function showReminderNotification(reminder) {
  const title = "Reminder";
  const body = reminder.notes ? `${reminder.title}\n${reminder.notes}` : reminder.title;

  if ("Notification" in window && Notification.permission === "granted") {
    new Notification(title, { body });
  }
  appendMessage("assistant", `Reminder: ${body}`);
}

async function pollDueReminders() {
  try {
    const response = await fetch("/reminders/due");
    const data = await response.json();
    for (const reminder of data.reminders || []) {
      showReminderNotification(reminder);
      await fetch(`/reminders/${reminder.id}/fired`, { method: "POST" });
    }
  } catch {
    // Keep polling quietly; chat should not be interrupted by transient errors.
  }
}

async function refreshSessions() {
  if (!sessionsList) {
    return;
  }
  try {
    const response = await fetch("/sessions");
    const data = await response.json();
    sessionsList.innerHTML = "";
    (data.sessions || []).forEach((session) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `session-button${session.id === sessionId ? " active" : ""}`;
      button.dataset.sessionId = session.id;

      const title = document.createElement("span");
      title.className = "session-title";
      title.textContent = session.title || "New chat";

      const date = document.createElement("span");
      date.className = "session-date";
      date.textContent = formatDate(session.updated_at);

      button.appendChild(title);
      button.appendChild(date);
      button.addEventListener("click", () => loadSession(session.id));
      sessionsList.appendChild(button);
    });
  } catch {
    sessionsList.innerHTML = "";
  }
}

async function loadSession(nextSessionId) {
  try {
    const response = await fetch(`/sessions/${nextSessionId}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error("Could not load chat.");
    }

    sessionId = nextSessionId;
    localStorage.setItem("assistant.sessionId", sessionId);
    history.splice(0, history.length);
    messages.innerHTML = "";

    const storedMessages = data.messages || [];
    if (!storedMessages.length) {
      appendMessage("assistant", "Ready. Tell me what you want to plan, write, or reason through.");
    }

    storedMessages.forEach((message) => {
      history.push(message);
      appendMessage(message.role, message.content);
    });
    refreshSessions();
  } catch (error) {
    appendMessage("assistant", error.message || "Could not load that chat.");
  }
}

async function sendMessage(message) {
  const cleanMessage = message.trim();
  if (!cleanMessage) {
    return;
  }

  appendMessage("user", cleanMessage);
  history.push({ role: "user", content: cleanMessage });

  input.value = "";
  autoSizeInput();
  input.focus();
  sendButton.disabled = true;

  const typing = appendMessage("assistant", "Thinking", { typing: true });

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: cleanMessage,
        session_id: sessionId,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }

    typing.remove();
    appendMessage("assistant", data.message || "");
    if (data.session_id) {
      sessionId = data.session_id;
      localStorage.setItem("assistant.sessionId", sessionId);
    }
    history.push({ role: "assistant", content: data.message || "" });
    refreshSessions();
  } catch (error) {
    typing.remove();
    appendMessage("assistant", error.message || "Something went wrong.");
  } finally {
    sendButton.disabled = false;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("input", autoSizeInput);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

clearButton.addEventListener("click", () => {
  resetMessages();
  input.focus();
});

newChatButton?.addEventListener("click", () => {
  sessionId = null;
  localStorage.removeItem("assistant.sessionId");
  resetMessages();
  refreshSessions();
  input.focus();
});

notifyButton?.addEventListener("click", requestNotificationPermission);

quickPrompts.forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.textContent.trim();
    autoSizeInput();
    input.focus();
  });
});

refreshHealth();
refreshTime();
refreshGoogleCalendarStatus();
refreshSessions();
if (sessionId) {
  loadSession(sessionId);
}
autoSizeInput();
setInterval(refreshTime, 30000);
setInterval(pollDueReminders, 10000);
pollDueReminders();
