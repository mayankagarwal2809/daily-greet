/**
 * Daily Greet — App Logic
 * Picks a unique greeting per day using a date-seeded index.
 * Supports browsing previous/next days.
 */

/** @type {Date} Currently displayed date */
let currentDate = new Date();

/**
 * Get the day-of-year index (0-365) for a given date.
 * @param {Date} date
 * @returns {number}
 */
function getDayOfYear(date) {
  const start = new Date(date.getFullYear(), 0, 0);
  const diff = date - start;
  const oneDay = 1000 * 60 * 60 * 24;
  return Math.floor(diff / oneDay);
}

/**
 * Simple seeded hash to shuffle greetings deterministically per year.
 * Avoids repeating the same greeting on the same calendar day each year.
 * @param {number} dayIndex
 * @param {number} year
 * @returns {number} Index into GREETINGS array
 */
function getGreetingIndex(dayIndex, year) {
  let seed = dayIndex * 2654435761 + year * 2246822519;
  seed = ((seed >>> 16) ^ seed) * 0x45d9f3b;
  seed = ((seed >>> 16) ^ seed) * 0x45d9f3b;
  seed = (seed >>> 16) ^ seed;
  return Math.abs(seed) % GREETINGS.length;
}

/**
 * Format a date nicely for display.
 * @param {Date} date
 * @returns {string}
 */
function formatDate(date) {
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Render the greeting for the current date.
 */
function renderGreeting() {
  const dayIndex = getDayOfYear(currentDate);
  const year = currentDate.getFullYear();
  const idx = getGreetingIndex(dayIndex, year);
  const greeting = GREETINGS[idx];

  document.getElementById('date-label').textContent = formatDate(currentDate);
  document.getElementById('day-count').textContent = `Day ${dayIndex} of ${isLeapYear(year) ? 366 : 365}`;
  document.getElementById('greeting-emoji').textContent = greeting.emoji;
  document.getElementById('greeting-text').textContent = greeting.text;
  document.getElementById('greeting-tip').textContent = `💡 Tip: ${greeting.tip}`;
  document.getElementById('greeting-category').textContent = greeting.category;

  // Re-trigger animation
  const card = document.querySelector('.greeting-card');
  card.classList.remove('slide-up');
  void card.offsetWidth; // force reflow
  card.classList.add('slide-up');
}

/**
 * Check if a year is a leap year.
 * @param {number} year
 * @returns {boolean}
 */
function isLeapYear(year) {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

/**
 * Change the displayed day by a delta (e.g., -1 for yesterday, +1 for tomorrow).
 * @param {number} delta
 */
function changeDay(delta) {
  currentDate.setDate(currentDate.getDate() + delta);
  renderGreeting();
}

/** Reset to today's greeting. */
function goToToday() {
  currentDate = new Date();
  renderGreeting();
}

/**
 * Copy the current greeting text to clipboard.
 */
async function copyGreeting() {
  const text = document.getElementById('greeting-text').textContent;
  const emoji = document.getElementById('greeting-emoji').textContent;
  const tip = document.getElementById('greeting-tip').textContent;

  const fullText = `${emoji} ${text}\n${tip}`;

  try {
    await navigator.clipboard.writeText(fullText);
    showToast('Copied to clipboard! Go share the love! 💛');
  } catch {
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = fullText;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('Copied to clipboard! 💛');
  }
}

/**
 * Share the greeting using the Web Share API or fall back to copy.
 */
async function shareGreeting() {
  const text = document.getElementById('greeting-text').textContent;
  const emoji = document.getElementById('greeting-emoji').textContent;

  const shareData = {
    title: 'Daily Greet ✨',
    text: `${emoji} ${text}`,
    url: window.location.href,
  };

  if (navigator.share) {
    try {
      await navigator.share(shareData);
    } catch (err) {
      if (err.name !== 'AbortError') {
        await copyGreeting();
      }
    }
  } else {
    await copyGreeting();
    showToast('Link copied — share it wherever you like! 🔗');
  }
}

/**
 * Show a toast notification at the bottom of the screen.
 * @param {string} message
 */
function showToast(message) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast bg-wgray-160 text-white text-sm font-semibold px-5 py-3 rounded-xl shadow-lg';
  toast.textContent = message;
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 2200);
}

// Keyboard navigation
document.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowLeft') changeDay(-1);
  if (e.key === 'ArrowRight') changeDay(1);
  if (e.key === 'Home' || e.key === 'Escape') goToToday();
});

// Initial render — wait for greetings to load
loadGreetings().then(() => renderGreeting());
