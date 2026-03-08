//EMAILI KONTROLLIMINE
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
//REGISTER
function registerUser() {
  const username = document.getElementById("regUsername").value;
  const email = document.getElementById("regEmail").value;
  const password = document.getElementById("regPassword").value;
  const responseEl = document.getElementById("registerResponse");
  const noteEl = document.getElementById("registerNote");

  if (!isValidEmail(email)) {
    responseEl.innerText = "Palun sisesta korrektne e-mail!";
    responseEl.style.color = "red";
    return;
  }

  if (!username || !email || !password) {
    responseEl.innerText = "Palun täida kõik väljad!";
    responseEl.style.color = "red";
    return;
  }

  fetch("/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  })
    .then((res) => res.json())
    .then((data) => {
      responseEl.innerText = data.message;
      responseEl.style.color = data.success ? "#00c896" : "#ff3b5c";

      if (data.note) {
        noteEl.innerText = data.note;
        noteEl.style.color = "#00c896";
      }

      if (data.success) {
        setTimeout(() => (window.location.href = "/"), 3000);
      }
    })

    .catch((err) => console.error("Fetch error:", err));
}

//LOGIN
function loginUser() {
  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;
  const responseEl = document.getElementById("response");

  responseEl.classList.remove("show");
  responseEl.style.color = "#3d4468";
  responseEl.innerText = "";

  fetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.redirect) {
        responseEl.innerText = "Tere tulemast! Suunamine...";
        responseEl.style.color = "#00c896";
        responseEl.classList.add("show");

        setTimeout(() => {
          window.location.href = data.redirect;
        }, 1000);
      } else {
        responseEl.innerText = data.message;
        responseEl.style.color = "#ff3b5c";
        responseEl.classList.add("show");
      }
    })

    .catch((err) => {
      console.error(err);
      responseEl.innerText = "Serveri viga!";
      responseEl.style.color = "#ff3b5c";
      responseEl.classList.add("show");
    });
}

//RESET
function resetPassword() {
  const email = document.getElementById("resetEmail").value;
  const responseEl = document.getElementById("resetResponse");
  const linkEl = document.getElementById("resetLink");
  const noteEl = document.getElementById("registerNote");
  document.getElementById("resetForm").addEventListener("submit", function (e) {
    e.preventDefault();
  });

  responseEl.innerText = "";
  linkEl.innerHTML = "";

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(email)) {
    responseEl.innerText = "Palun sisesta korrektne e-mail!";
    responseEl.style.color = "red";
    return;
  }

  fetch(window.location.origin + "/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.reset_link) {
        responseEl.innerText = data.message;
        responseEl.style.display = "block";
        responseEl.style.visibility = "visible";
        responseEl.style.opacity = "1";
        responseEl.style.color = "black";
      } else {
        responseEl.innerHTML = `
    ${data.message}<br>
    <small>Suunan tagasi avalehele 5 sekundi pärast...</small>
  `;
        responseEl.style.color = "green";

        setTimeout(() => (window.location.href = "/"), 5000);
      }
    })

    .catch((err) => {
      console.error(err);
      responseEl.innerText = "Serveri viga!";
      responseEl.style.color = "#ff3b5c";
    });
}

//UUS PAROOL
function setNewPassword() {
  const password = document.getElementById("newPassword").value;
  const responseEl = document.getElementById("passwordResponse");

  responseEl.innerText = "";

  if (!password) {
    responseEl.innerText = "Palun sisesta parool!";
    responseEl.style.color = "red";
    return;
  }

  if (password.length < 8) {
    responseEl.innerText = "Parool peab olema vähemalt 8 tähemärki!";
    responseEl.style.color = "red";
    return;
  }

  fetch(window.location.href, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: password }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.message) {
        responseEl.innerHTML = `
    ${data.message}<br>
    <small>Suunan tagasi avalehele 3 sekundi pärast...</small>
  `;
        responseEl.style.color = "green";
        setTimeout(() => (window.location.href = "/"), 3000);
      } else {
        responseEl.innerText = "Viga parooli muutmisel!";
        responseEl.style.color = "red";
      }
    })
    .catch((err) => {
      console.error(err);
      responseEl.innerText = "Serveri viga!";
      responseEl.style.color = "#ff3b5c";
    });
}
//kuupäev
document.addEventListener("DOMContentLoaded", () => {
  flatpickr("#taskDate", {
    dateFormat: "d/m/Y",
    defaultDate: "today",
    locale: "et",
    onChange: loadTasks,
  });

  loadTasks();
});

function formatToISO(dateStr) {
  const [d, m, y] = dateStr.split("/");
  return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
}
//dropdown inimesed
async function loadPersons() {
  const response = await fetch("/get-persons");
  const persons = await response.json();

  const select1 = document.getElementById("personSelect");
  const select2 = document.getElementById("emailPersonSelect");

  if (select1) {
    select1.innerHTML = '<option value="">Vali inimene</option>';
    persons.forEach((p) => {
      select1.innerHTML += `<option value="${p[0]}">${p[1]}</option>`;
    });
  }

  if (select2) {
    select2.innerHTML = '<option value="">Vali inimene</option>';
    persons.forEach((p) => {
      select2.innerHTML += `<option value="${p[0]}">${p[1]}</option>`;
    });
  }
}
//lisa uus
async function addPerson() {
  const name = document.getElementById("personName").value.trim();
  const email = document.getElementById("personEmail").value.trim();

  if (!name || !email) {
    alert("Täida vähemalt nimi ja e-mail!");
    return;
  }

  const password = ""; //genereerib parooli

  try {
    const response = await fetch("/add-person", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });

    const data = await response.json();

    if (data.success) {
      alert("Töötaja lisatud! Kontrolli e-maili.");
      document.getElementById("personName").value = "";
      document.getElementById("personEmail").value = "";

      loadPersons();
    } else {
      alert(data.error || data.message || "Tekkis viga");
    }
  } catch (err) {
    console.error(err);
    alert("Serveri viga!");
  }
}

//LISA ÜL
async function addTask() {
  const taskDateEl = document.getElementById("taskDate");
  const descriptionEl = document.getElementById("description");
  const personSelectEl = document.getElementById("personSelect");
  if (!taskDateEl || !descriptionEl || !personSelectEl) return;

  const date = formatToISO(taskDateEl.value);
  const description = descriptionEl.value.trim();
  const location = document.getElementById("location")?.value || "";
  const contact = document.getElementById("contact")?.value || "";
  const personId = personSelectEl.value;

  if (!date || !description || !personId) {
    alert("Täida kuupäev, kirjeldus ja vali inimene!");
    return;
  }

  await fetch("/add-task", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      date,
      description,
      location,
      contact,
      person_id: personId,
    }),
  });

  descriptionEl.value = "";
  document.getElementById("location") &&
    (document.getElementById("location").value = "");
  document.getElementById("contact") &&
    (document.getElementById("contact").value = "");

  loadTasks();
}

//NÄITA ÜL
async function loadTasks() {
  const taskDateEl = document.getElementById("taskDate");
  const personSelectEl = document.getElementById("personSelect");
  const list = document.getElementById("taskList");
  if (!taskDateEl || !personSelectEl || !list) return;

  const date = formatToISO(taskDateEl.value);
  const personId = personSelectEl.value;

  const url = personId
    ? `/get-tasks/${date}?person_id=${personId}`
    : `/get-tasks/${date}`;
  const res = await fetch(url);
  const tasks = await res.json();

  list.innerHTML = "";

  const tasksByPerson = {};
  tasks.forEach((task) => {
    const personName = task[1];
    if (!tasksByPerson[personName]) tasksByPerson[personName] = [];
    tasksByPerson[personName].push(task);
  });

  for (const personName in tasksByPerson) {
    const personDiv = document.createElement("div");
    personDiv.className = "person-box";

    const personHeader = document.createElement("strong");
    personHeader.innerText = personName;
    personDiv.appendChild(personHeader);

    tasksByPerson[personName].forEach((task) => {
      const completed = task[5] !== null ? Number(task[5]) : null;
      let textClass = "default-text";
      if (completed === 1) textClass = "done-text";
      else if (completed === 0) textClass = "not-done-text";

      const taskDiv = document.createElement("div");
      taskDiv.className = `task ${textClass}`;
      taskDiv.innerHTML = `
        <div>${task[2]}</div>
        <div>${task[3] || ""}</div>
        <div>${task[4] || ""}</div>
        <div class="task-buttons">
          <button onclick="markDone(${task[0]})">Tehtud</button>
          <button onclick="markNotDone(${task[0]})">Tegemata</button>
          <button onclick="deleteTask(${task[0]})">Kustuta</button>
        </div>
      `;
      personDiv.appendChild(taskDiv);
    });

    list.appendChild(personDiv);
  }
}
//SAADA KIRI
function sendTasksEmail() {
  const personId = document.getElementById("personSelect").value;
  if (!personId) {
    alert("Vali inimene!");
    return;
  }

  fetch(`/send-tasks-email/${personId}`, { method: "POST" })
    .then((res) => res.json())
    .then((data) =>
      data.success
        ? alert(`E-mail saadetud! Ülesandeid: ${data.count}`)
        : alert(`Viga: ${data.message}`),
    )
    .catch((err) => {
      console.error(err);
      alert("Serveri viga!");
    });
}

//STAATUSE NUPUD
function markDone(id) {
  fetch(`/mark-done/${id}`, { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) loadTasks();
    });
}

function markNotDone(id) {
  fetch(`/mark-not-done/${id}`, { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) loadTasks();
    });
}

function deleteTask(id) {
  fetch(`/delete-task/${id}`, { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) loadTasks();
    });
}

document.addEventListener("DOMContentLoaded", () => {
  // Flatpickr
  const taskDateEl = document.getElementById("taskDate");

  if (taskDateEl && typeof flatpickr !== "undefined") {
    flatpickr(taskDateEl, {
      dateFormat: "d/m/Y",
      defaultDate: "today",
      locale: "et",
      onChange: loadTasks,
    });
    loadTasks();
  }

  //LISAMINE
  const addWorkerBtn = document.getElementById("addWorkerBtn");
  if (addWorkerBtn) {
    addWorkerBtn.addEventListener("click", async () => {
      const nameEl = document.getElementById("workerName");
      const emailEl = document.getElementById("workerEmail");
      if (!nameEl || !emailEl) return;

      const name = nameEl.value.trim();
      const email = emailEl.value.trim();
      if (!name || !email) return alert("Täida nii nimi kui e-mail!");

      const res = await fetch("/add-person", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password: "" }),
      });
      const data = await res.json();
      if (data.success) {
        alert(`Töötaja lisatud! Kontrolli e-maili: ${email}`);
        nameEl.value = "";
        emailEl.value = "";
        loadPersons();
      } else {
        alert(data.error || data.message || "Tekkis viga!");
      }
    });
  }

  function sendTasksEmail() {
    const personId = document.getElementById("personSelect").value;
    if (!personId) {
      alert("Vali inimene!");
      return;
    }

    fetch(`/send-tasks-email/${personId}`, {
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          alert(`E-mail saadetud! Ülesandeid: ${data.count}`);
        } else {
          alert(`Viga: ${data.message}`);
        }
      })
      .catch((err) => {
        console.error(err);
        alert("Serveri viga!");
      });
  }

  const workerLoginBtn = document.getElementById("workerLoginBtn");
  if (workerLoginBtn) {
    workerLoginBtn.addEventListener("click", () => {
      window.location.href = "/worker-login";
    });
  }
});

loadTasks();
