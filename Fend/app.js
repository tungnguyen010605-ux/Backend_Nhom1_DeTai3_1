const form = document.getElementById("tryon-form");
const submitBtn = document.getElementById("submit-btn");
const statusLog = document.getElementById("status-log");
const resultLink = document.getElementById("result-link");
const resultImage = document.getElementById("result-image");
const existingUserSelect = document.getElementById("existing-user-select");
const existingClothingSelect = document.getElementById("existing-clothing-select");
const existingUserGroup = document.getElementById("existing-user-group");
const existingClothingGroup = document.getElementById("existing-clothing-group");
const refreshUsersBtn = document.getElementById("refresh-users");
const refreshClothingBtn = document.getElementById("refresh-clothing");

let usersCache = [];
let clothingCache = [];

function log(message) {
  statusLog.textContent += `\n${message}`;
}

function resetUi() {
  statusLog.textContent = "Starting...";
  resultLink.textContent = "No result yet.";
  resultImage.style.display = "none";
  resultImage.removeAttribute("src");
}

function selectedMode(name) {
  const el = form.querySelector(`input[name="${name}"]:checked`);
  return el ? el.value : "";
}

function fillSelect(selectEl, options, emptyText) {
  selectEl.innerHTML = "";
  if (options.length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = emptyText;
    selectEl.appendChild(option);
    return;
  }

  options.forEach((entry) => {
    const option = document.createElement("option");
    option.value = String(entry.value);
    option.textContent = entry.label;
    selectEl.appendChild(option);
  });
}

function syncModeVisibility() {
  const userMode = selectedMode("user_mode");
  const clothingMode = selectedMode("clothing_mode");
  existingUserGroup.style.display = userMode === "existing" ? "grid" : "none";
  existingClothingGroup.style.display = clothingMode === "existing" ? "grid" : "none";
}

async function apiJson(url, options) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data && data.detail ? JSON.stringify(data.detail) : response.statusText;
    throw new Error(`${response.status} ${detail}`);
  }
  return data;
}

async function pollTask(taskId, maxTries = 30, delayMs = 500) {
  for (let i = 0; i < maxTries; i += 1) {
    const status = await apiJson(`/status/${taskId}`, { method: "GET" });
    log(`Task ${status.status} (${status.progress}%) - ${status.message}`);

    if (status.status === "completed") {
      return status;
    }
    if (status.status === "failed") {
      throw new Error(status.message || "Task failed");
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  throw new Error("Task did not complete in time");
}

async function loadUsers() {
  usersCache = await apiJson("/users?limit=500", { method: "GET" });
  fillSelect(
    existingUserSelect,
    usersCache.map((u) => ({ value: u.id, label: `#${u.id} - ${u.name}` })),
    "No users found. Switch to Create new user.",
  );
}

async function loadClothing() {
  const selectedUserId = Number(existingUserSelect.value);
  const hasUser = Number.isFinite(selectedUserId) && selectedUserId > 0;
  const url = hasUser ? `/clothing-items?user_id=${selectedUserId}&limit=500` : "/clothing-items?limit=500";

  clothingCache = await apiJson(url, { method: "GET" });
  fillSelect(
    existingClothingSelect,
    clothingCache.map((c) => ({
      value: c.id,
      label: `#${c.id} - user ${c.user_id} - ${c.category}/${c.size_label}/${c.color}`,
    })),
    "No clothing items found. Switch to Create new clothing item.",
  );
}

function requireNumber(formData, name, message) {
  const value = Number(formData.get(name));
  if (!Number.isFinite(value)) {
    throw new Error(message);
  }
  return value;
}

async function resolveUserId(formData) {
  if (selectedMode("user_mode") === "existing") {
    const userId = Number(existingUserSelect.value);
    if (!Number.isFinite(userId) || userId <= 0) {
      throw new Error("Please select an existing user");
    }
    log(`Using existing user: id=${userId}`);
    return userId;
  }

  const name = String(formData.get("name") || "").trim();
  if (!name) {
    throw new Error("Please enter user name");
  }

  const userPayload = {
    name,
    height_cm: requireNumber(formData, "height_cm", "Please enter valid height"),
    chest_cm: requireNumber(formData, "chest_cm", "Please enter valid chest"),
    waist_cm: requireNumber(formData, "waist_cm", "Please enter valid waist"),
    hip_cm: requireNumber(formData, "hip_cm", "Please enter valid hip"),
    inseam_cm: requireNumber(formData, "inseam_cm", "Please enter valid inseam"),
  };

  log("1) Creating user profile...");
  const user = await apiJson("/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(userPayload),
  });

  log(`User created: id=${user.id}`);
  await loadUsers();
  existingUserSelect.value = String(user.id);
  return user.id;
}

async function resolveClothingId(formData, userId) {
  if (selectedMode("clothing_mode") === "existing") {
    const clothingId = Number(existingClothingSelect.value);
    if (!Number.isFinite(clothingId) || clothingId <= 0) {
      throw new Error("Please select an existing clothing item");
    }

    const item = clothingCache.find((c) => c.id === clothingId);
    if (item && item.user_id !== userId) {
      throw new Error("Selected clothing item does not belong to selected user");
    }

    log(`Using existing clothing item: id=${clothingId}`);
    return clothingId;
  }

  const file = formData.get("file");
  if (!(file instanceof File) || file.size === 0) {
    throw new Error("Please choose a clothing image file for new clothing item");
  }

  const width = Number(formData.get("width"));
  const height = Number(formData.get("height"));
  const normalize = formData.get("normalize") === "on";
  const augment = formData.get("augment") === "on";

  log("2) Preprocessing clothing image...");
  const imageForm = new FormData();
  imageForm.append("file", file);
  const preprocess = await apiJson(
    `/preprocess?width=${width}&height=${height}&normalize=${normalize}&augment=${augment}`,
    {
      method: "POST",
      body: imageForm,
    },
  );

  log(`Image preprocessed: ${preprocess.file_url}`);

  const clothPayload = {
    user_id: userId,
    category: String(formData.get("category") || "shirt"),
    size_label: String(formData.get("size_label") || "M"),
    color: String(formData.get("color") || "blue"),
    image_path: preprocess.file_url,
  };

  log("3) Creating clothing item...");
  const cloth = await apiJson("/clothing-items", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(clothPayload),
  });

  log(`Clothing item created: id=${cloth.id}`);
  await loadClothing();
  existingClothingSelect.value = String(cloth.id);
  return cloth.id;
}

async function runFlow(event) {
  event.preventDefault();
  submitBtn.disabled = true;
  resetUi();

  try {
    const formData = new FormData(form);
    const userId = await resolveUserId(formData);
    const clothingId = await resolveClothingId(formData, userId);

    log("4) Starting texture generation task...");
    const task = await apiJson("/tasks/generate-texture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, clothing_item_id: clothingId }),
    });

    log(`Task queued: task_id=${task.task_id}`);

    log("5) Polling task status...");
    const completed = await pollTask(task.task_id);

    const absoluteUrl = `${window.location.origin}${completed.output_url}`;
    resultLink.innerHTML = `Output: <a href="${absoluteUrl}" target="_blank" rel="noopener">${completed.output_url}</a>`;
    resultImage.src = absoluteUrl;
    resultImage.style.display = "block";
    log("Done.");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    log(`Error: ${message}`);
  } finally {
    submitBtn.disabled = false;
  }
}

form.addEventListener("submit", runFlow);
form.addEventListener("change", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }

  if (target.matches('input[name="user_mode"]') || target.matches('input[name="clothing_mode"]')) {
    syncModeVisibility();
  }
});

existingUserSelect.addEventListener("change", async () => {
  try {
    await loadClothing();
  } catch (error) {
    log(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
});

refreshUsersBtn.addEventListener("click", async () => {
  try {
    await loadUsers();
    await loadClothing();
  } catch (error) {
    log(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
});

refreshClothingBtn.addEventListener("click", async () => {
  try {
    await loadClothing();
  } catch (error) {
    log(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
});

async function initialize() {
  syncModeVisibility();
  statusLog.textContent = "Ready.";

  try {
    await loadUsers();
    await loadClothing();
  } catch (error) {
    log(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
}

initialize();

