/**
 * Load greetings from the shared JSON file.
 * Both the web app and the Slack bot use greetings.json as the single source of truth.
 */
let GREETINGS = [];

async function loadGreetings() {
  const response = await fetch('greetings.json');
  GREETINGS = await response.json();
}
