// ==========================================
// 1. MENU & THEME LOGIC
// ==========================================
function toggleMenu() {
  document.getElementById("myDropdown").classList.toggle("show");
}

function toggleTheme() {
  const body = document.body;
  body.classList.toggle("dark-mode");
  localStorage.setItem("theme", body.classList.contains("dark-mode") ? "dark" : "light");
}

if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark-mode");
}

// Close menu/modals if clicked outside
window.onclick = function(event) {
  if (!event.target.matches('.menu-btn')) {
    const dropdowns = document.getElementsByClassName("dropdown-content");
    for (let i = 0; i < dropdowns.length; i++) {
      if (dropdowns[i].classList.contains('show')) dropdowns[i].classList.remove('show');
    }
  }
  const addModal = document.getElementById("addCameraModal");
  const editModal = document.getElementById("editCameraModal");
  if (event.target == addModal) closeAddCamera();
  if (event.target == editModal) closeEditModal();
}

// ==========================================
// 2. AUTO/MANUAL MODE LOGIC (Fixed)
// ==========================================
function setMode(mode) {
  // Mode change request bhejo (Backend par logic hona chahiye, abhi sirf console log)
  console.log("Mode changed to:", mode);
  // Future: fetch('/set_mode', ...)
}

// ==========================================
// 3. CAMERA & MODAL LOGIC
// ==========================================
function setGreen(cameraId) {
  fetch("/set_green", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: cameraId })
  });
}

// Add Camera Modal
function openAddCamera() { document.getElementById("addCameraModal").style.display = "flex"; }
function closeAddCamera() { document.getElementById("addCameraModal").style.display = "none"; }

function saveCamera() {
  const name = document.getElementById("camName").value;
  const ip = document.getElementById("camPath").value;
  const hubId = document.getElementById("currentHubId").value;

  if (!name || !ip) { alert("Fill all fields"); return; }

  fetch("/add_camera", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, ip, hub_id: hubId })
  }).then(res => res.json()).then(data => { if(data.ok) location.reload(); });
}

// Edit Camera Modal
let currentEditId = null;
function openEditModal(id, name, ip) {
  currentEditId = id;
  document.getElementById("editCamId").value = id;
  document.getElementById("editCamName").value = name;
  document.getElementById("editCamPath").value = ip;
  document.getElementById("editCameraModal").style.display = "flex";
}
function closeEditModal() { document.getElementById("editCameraModal").style.display = "none"; }

function saveEditCamera() {
  const name = document.getElementById("editCamName").value;
  const ip = document.getElementById("editCamPath").value;
  fetch("/edit_camera", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: currentEditId, name, ip })
  }).then(res => res.json()).then(data => { if(data.success) location.reload(); });
}

function confirmDelete() {
  if(confirm("Delete this camera?")) {
    fetch("/delete_camera", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: currentEditId })
    }).then(res => res.json()).then(data => { if(data.success) location.reload(); });
  }
}

// Live Updates
function pollState() {
  fetch("/state").then(res => res.json()).then(data => {
    Object.entries(data.cameras).forEach(([id, cam]) => {
      const card = document.querySelector(`.card[data-cid="${id}"]`);
      if (card) {
        card.classList.remove("red", "yellow", "green");
        card.classList.add(cam.light);
        
        const dot = card.querySelector(".status-dot");
        if(dot) { dot.classList.remove("red", "yellow", "green"); dot.classList.add(cam.light); }
        
        const text = card.querySelector(".light-text");
        if (text) text.innerText = cam.light.toUpperCase();
      }
    });
  });
}
setInterval(pollState, 1000);