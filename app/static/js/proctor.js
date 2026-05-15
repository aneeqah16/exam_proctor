/**
 * proctor.js
 * Runs silently during the student exam session.
 * Detects: tab switching, idle time.
 * Also handles the countdown timer and auto-submit.
 */

const proctorData = document.getElementById("proctor-data");
const attemptId   = parseInt(proctorData.dataset.attemptId);
const examMins    = parseInt(proctorData.dataset.duration);

const LOG_URL = "/proctor/log-event";


// ── Send event to Flask backend ───────────────────────────────────────────────
function sendEvent(eventType) {
    fetch(LOG_URL, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({
            attempt_id: attemptId,
            event_type: eventType
        })
    })
    .then(res => res.json())
    .then(data => console.log("[Proctor] Logged:", data.event))
    .catch(err => console.warn("[Proctor] Failed:", err));
}


// ── Tab switch detection ──────────────────────────────────────────────────────
document.addEventListener("visibilitychange", function() {
    if (document.hidden) {
        sendEvent("tab_switch");
        // Pause idle tracking while tab is hidden
        clearTimeout(idleTimer);
        idleTimer = null;
    } else {
        // Resume idle tracking when student comes back
        resetIdle();
    }
});


// ── Idle detection ────────────────────────────────────────────────────────────
// Idle = no mouse/keyboard activity for 60 seconds WHILE tab is visible
const IDLE_LIMIT = 60 * 1000;
let idleTimer = null;
let lastActivity = Date.now();

function resetIdle() {
    // Don't start idle timer if tab is hidden
    if (document.hidden) return;

    lastActivity = Date.now();
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function() {
        sendEvent("idle");
        // Keep firing every 60s as long as still idle
        idleTimer = setTimeout(arguments.callee, IDLE_LIMIT);
    }, IDLE_LIMIT);
}

["mousemove", "keydown", "click", "scroll"].forEach(function(evt) {
    document.addEventListener(evt, resetIdle, { passive: true });
});

resetIdle(); // Start immediately


// ── Countdown timer ───────────────────────────────────────────────────────────
let totalSeconds   = examMins * 60;
const timerDisplay = document.getElementById("timer-display");
const examForm     = document.getElementById("exam-form");

function updateTimer() {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;

    timerDisplay.textContent =
        String(mins).padStart(2, "0") + ":" +
        String(secs).padStart(2, "0");

    if (totalSeconds <= 300) timerDisplay.style.color = "#856404";
    if (totalSeconds <= 60)  timerDisplay.style.color = "#7B1A1A";

    if (totalSeconds <= 0) {
        clearInterval(timerInterval);
        timerDisplay.textContent = "00:00";
        if (examForm) examForm.submit();
        return;
    }

    totalSeconds--;
}

updateTimer();
const timerInterval = setInterval(updateTimer, 1000);