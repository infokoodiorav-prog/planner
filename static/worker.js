document.addEventListener("DOMContentLoaded", () => {
  const taskList = document.getElementById("taskList");
  const filterEl = document.getElementById("filterTasks");
  const taskDateEl = document.getElementById("taskDate");
  const logoutBtn = document.getElementById("logoutBtn");

  flatpickr("#taskDate", {
    dateFormat: "d/m/Y",
    defaultDate: "today",
    locale: "et",
    onChange: loadTasks,
  });

  if (filterEl) filterEl.addEventListener("change", loadTasks);

  if (logoutBtn)
    logoutBtn.addEventListener(
      "click",
      () => (window.location.href = "/worker-logout"),
    );

  if (taskList) {
    taskList.addEventListener("click", (e) => {
      const taskDiv = e.target.closest(".task");
      if (!taskDiv) return;
      const taskId = taskDiv.dataset.taskId;

      if (e.target.classList.contains("mark-done-btn")) {
        const url =
          e.target.textContent === "Tehtud"
            ? `/mark-done/${taskId}`
            : `/mark-not-done/${taskId}`;
        fetch(url, { method: "POST", credentials: "same-origin" })
          .then((r) => r.json())
          .then((d) => {
            if (d.success) loadTasks();
          });
      }

      if (e.target.classList.contains("delete-btn")) {
        if (!confirm("Kas oled kindel, et soovid ülesande kustutada?")) return;
        fetch(`/delete-task/${taskId}`, {
          method: "POST",
          credentials: "same-origin",
        })
          .then((r) => r.json())
          .then((d) => {
            if (d.success) loadTasks();
          });
      }
    });
  }
  loadTasks();
});

function formatToISO(value) {
  if (!value) return "";
  const [day, month, year] = value.split("/");
  return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
}

async function login() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const responseEl = document.getElementById("response");
  responseEl.classList.remove("show");
  responseEl.style.color = "#3d4468";
  responseEl.innerText = "";

  if (!email || !password) {
    responseEl.innerText = "Täida kõik väljad!";
    responseEl.style.color = "#ff3b5c";
    responseEl.classList.add("show");
    return;
  }

  try {
    const res = await fetch("/worker-login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();

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
  } catch (err) {
    console.error(err);
    responseEl.innerText = "Serveri viga!";
    responseEl.style.color = "#ff3b5c";
    responseEl.classList.add("show");
  }
}

async function loadTasks() {
  const list = document.getElementById("taskList");
  const filterEl = document.getElementById("filterTasks");
  const taskDateEl = document.getElementById("taskDate");
  if (!list) return;

  const filter = filterEl ? filterEl.value : "all";
  const date = formatToISO(taskDateEl.value);

  try {
    const res = await fetch("/get-tasks-worker", {
      credentials: "same-origin",
    });
    const text = await res.text();

    // Kontrollime, kas see on JSON või HTML (login page)
    let tasks;
    try {
      tasks = JSON.parse(text);
    } catch (e) {
      console.error("Server tagastas mitte-JSONi:", text);
      list.innerHTML = `<div style="color:red;">Tööülesandeid ei saa laadida. Kontrolli loginit.</div>`;
      return;
    }

    list.innerHTML = "";
    let total = 0,
      done = 0;

    tasks.forEach((t) => {
      if (date && t.task_date !== date) return;
      if (filter === "done" && t.completed != 1) return;
      if (filter === "todo" && t.completed == 1) return;

      total++;
      if (t.completed == 1) done++;

      const taskDiv = document.createElement("div");
      taskDiv.className = `task ${t.completed == 1 ? "done-text" : "not-done-text"}`;
      taskDiv.dataset.taskId = t.id;

      taskDiv.innerHTML = `
        <div><strong>${t.description}</strong></div>
        <div>${t.task_date}</div>
        <div>${t.location || "-"}</div>
        <div>${t.contact || "-"}</div>
        <div class="task-buttons">
          <button class="mark-done-btn">Tehtud</button>
      <button class="mark-not-done-btn">Tegemata</button>
        </div>
      `;

      list.appendChild(taskDiv);
    });

    document.getElementById("totalTasks").innerText = total;
    document.getElementById("doneTasks").innerText = done;
    document.getElementById("todoTasks").innerText = total - done;
    document.getElementById("progressFill").style.width = total
      ? Math.round((done / total) * 100) + "%"
      : "0%";
  } catch (err) {
    console.error("Viga ülesannete laadimisel:", err);
    list.innerHTML = `<div style="color:red;">Ülesandeid ei saa laadida. Serveri viga.</div>`;
  }
}

// Alglaadimine
loadTasks();

// Delegatsioon nupuvajutustele
taskList.addEventListener("click", (e) => {
  const taskDiv = e.target.closest(".task");
  if (!taskDiv) return;
  const taskId = taskDiv.dataset.taskId;

  // Märgi tehtuks
  if (e.target.classList.contains("mark-done-btn")) {
    fetch(`/mark-done/${taskId}`, {
      method: "POST",
      credentials: "same-origin",
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.success) loadTasks();
      });
  }

  // Märgi tegemata
  if (e.target.classList.contains("mark-not-done-btn")) {
    fetch(`/mark-not-done/${taskId}`, {
      method: "POST",
      credentials: "same-origin",
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.success) loadTasks();
      });
  }
});
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
document.getElementById("filterTasks").addEventListener("change", loadTasks);

function logout() {
  window.location.href = "/worker-logout";
}
