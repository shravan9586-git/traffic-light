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

// Apply theme on load
if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark-mode");
}

// ==========================================
// 2. USER MODAL FUNCTIONS
// ==========================================
function openUserModal() {
  document.getElementById("myDropdown").classList.remove("show"); // Close menu
  document.getElementById("userModal").style.display = "flex";
}

function closeUserModal() {
  document.getElementById("userModal").style.display = "none";
}

function createUser() {
  const username = document.getElementById("new_user").value;
  const password = document.getElementById("new_pass").value;
  const role = document.getElementById("new_role").value;

  if(!username || !password) { alert("Please fill all fields"); return; }

  fetch("/create_user", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ username, password, role })
  })
  .then(res => res.json())
  .then(data => {
    if(data.success) {
      location.reload();
    } else {
      alert("Error: " + data.error);
    }
  });
}

// ==========================================
// 3. ADD HUB MODAL FUNCTIONS (No Prompt!)
// ==========================================
function openHubModal() {
  document.getElementById("hubModal").style.display = "flex";
  // Focus on input immediately
  setTimeout(() => document.getElementById("new_hub_name").focus(), 100);
}

function closeHubModal() {
  document.getElementById("hubModal").style.display = "none";
  document.getElementById("new_hub_name").value = ""; // Clear input
}

function submitNewHub() {
  const name = document.getElementById("new_hub_name").value;

  if (!name || name.trim() === "") {
    alert("Hub name is required!");
    return;
  }

  fetch("/add_hub", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ name: name })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      location.reload();
    } else {
      alert("Failed to add hub");
    }
  });
}

// ==========================================
// 4. DELETE HUB
// ==========================================
function deleteHub(id) {
  if(!confirm("Delete this Hub?")) return;
  
  fetch("/delete_hub", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({id})
  }).then(() => location.reload());
}

// Close modals when clicking outside
window.onclick = function(event) {
  const userModal = document.getElementById("userModal");
  const hubModal = document.getElementById("hubModal");
  
  if (event.target == userModal) closeUserModal();
  if (event.target == hubModal) closeHubModal();
  
  if (!event.target.matches('.menu-btn')) {
    const dropdowns = document.getElementsByClassName("dropdown-content");
    for (let i = 0; i < dropdowns.length; i++) {
      if (dropdowns[i].classList.contains('show')) dropdowns[i].classList.remove('show');
    }
  }
}

// ==========================================
// CHANGE PASSWORD LOGIC
// ==========================================
function openPasswordModal() {
  // Menu band karo
  document.getElementById("myDropdown").classList.remove("show");
  // Modal kholo
  document.getElementById("passwordModal").style.display = "flex";
}

function closePasswordModal() {
  document.getElementById("passwordModal").style.display = "none";
  // Fields clear kar do
  document.getElementById("oldPass").value = "";
  document.getElementById("newPass").value = "";
}

function submitPasswordChange() {
  const oldPass = document.getElementById("oldPass").value;
  const newPass = document.getElementById("newPass").value;

  if (!oldPass || !newPass) {
    alert("Please fill both fields");
    return;
  }

  fetch("/change_password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ old_password: oldPass, new_password: newPass })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert("Password Updated Successfully!");
      closePasswordModal();
    } else {
      alert("Error: " + data.error);
    }
  })
  .catch(err => console.error(err));
}

// Window click listener me bhi add karein taaki bahar click karne par band ho
// (Jo purana window.onclick hai, usme ye line add kar sakte hain):
// if (event.target == document.getElementById("passwordModal")) closePasswordModal();