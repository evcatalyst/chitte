let eventsData = [];
let sources = [];
let lastUpdated = "";

function fetchEvents() {
  document.getElementById("loading").style.display = "block";
  document.getElementById("error").style.display = "none";
  fetch("events.json")
    .then(res => {
      if (!res.ok) throw new Error("Network response was not ok");
      return res.json();
    })
    .then(data => {
      eventsData = data.events || [];
      sources = data.sources || [];
      lastUpdated = data.last_updated || "";
      document.getElementById("loading").style.display = "none";
      renderEvents();
      renderFooter();
    })
    .catch(err => {
      document.getElementById("loading").style.display = "none";
      document.getElementById("error").style.display = "block";
      console.error("Failed to load events.json:", err);
    });
}

function renderEvents() {
  const sortBy = document.getElementById("sort").value;
  const tbody = document.getElementById("event-body");
  tbody.innerHTML = "";
  let sorted = [...eventsData];
  if (sortBy === "date") {
    sorted.sort((a, b) => new Date(a.date) - new Date(b.date));
  } else if (sortBy === "venue") {
    sorted.sort((a, b) => a.venue.localeCompare(b.venue));
  }
  sorted.forEach(event => {
    const newBadge = event.is_new ? '<span class="new-chitte">new chitte!</span>' : '';
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${event.date}</td>
      <td>${event.time}</td>
      <td class="venue-click" data-venue='${JSON.stringify(event.venue_info)}' data-name='${event.venue}'>${event.venue}</td>
      <td class="event-click" data-desc='${event.description}' data-link='${event.link}'>${event.description} ${newBadge}</td>
      <td>${event.category}</td>
    `;
    tbody.appendChild(row);
  });
  // add click listeners
  document.querySelectorAll(".event-click").forEach(td => {
    td.addEventListener("click", e => showEventModal(e.target.dataset.desc, e.target.dataset.link));
  });
  document.querySelectorAll(".venue-click").forEach(td => {
    td.addEventListener("click", e => {
      const venue = JSON.parse(e.target.dataset.venue);
      showVenueModal(e.target.dataset.name, venue);
    });
  });
}

function renderFooter() {
  document.getElementById("lastUpdated").textContent = lastUpdated ? formatDate(lastUpdated) : "unknown";
}

function formatDate(dt) {
  // dt: "2025-08-08T00:00:00Z"
  const d = new Date(dt);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
}

// Modals
function showEventModal(desc, link) {
  document.getElementById("eventTitle").textContent = "event details";
  document.getElementById("eventDetails").textContent = desc;
  document.getElementById("eventLink").href = link;
  document.getElementById("eventModal").style.display = "block";
}
function showVenueModal(name, info) {
  document.getElementById("venueName").textContent = name;
  document.getElementById("venuePhoto").src = info.photo_url;
  document.getElementById("venueInfo").textContent = info.description;
  document.getElementById("yelpLink").href = info.yelp_url;
  document.getElementById("mapsLink").href = info.maps_url;
  document.getElementById("directionsLink").href = info.maps_url + "&dirflg=d";
  document.getElementById("venueModal").style.display = "block";
}
function showSourcesModal() {
  const list = document.getElementById("sourcesList");
  list.innerHTML = "";
  sources.forEach(source => {
    const li = document.createElement("li");
    li.innerHTML = `<a href="${source.url}" target="_blank">${source.title}</a>`;
    list.appendChild(li);
  });
  document.getElementById("sourcesModal").style.display = "block";
}
function closeModal(id) {
  document.getElementById(id).style.display = "none";
}

// Theme changer
function changeTheme(theme) {
  document.body.className = `theme-${theme}`;
  renderEvents();
}

// Event listeners
document.getElementById("theme").addEventListener("change", e => changeTheme(e.target.value));
document.getElementById("applyBtn").addEventListener("click", renderEvents);
document.getElementById("sourcesLink").addEventListener("click", showSourcesModal);
document.getElementById("closeEvent").addEventListener("click", () => closeModal("eventModal"));
document.getElementById("closeVenue").addEventListener("click", () => closeModal("venueModal"));
document.getElementById("closeSources").addEventListener("click", () => closeModal("sourcesModal"));

// Initial load
fetchEvents();
