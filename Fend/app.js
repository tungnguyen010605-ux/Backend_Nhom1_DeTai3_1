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
const autoPickClothingBtn = document.getElementById("auto-pick-clothing");

const categoryGroupSelect = document.getElementById("category-group-select");
const categoryTypeSelect = document.getElementById("category-type-select");
const sizeSelect = document.getElementById("size-select");
const colorSelect = document.getElementById("color-select");
const imagePathPreviewInput = document.getElementById("image-path-preview");
const clothingFileInput = document.getElementById("clothing-file");

const CATEGORY_TREE = {
  shirt: {
    label: "Áo",
    types: [
      { value: "polo", label: "Áo polo" },
      { value: "tshirt", label: "Áo T-shirt" },
      { value: "shirt", label: "Áo sơ mi" },
      { value: "hoodie", label: "Áo hoodie" },
      { value: "jacket", label: "Áo khoác" },
      { value: "other", label: "Loại áo khác" },
    ],
  },
  pants: {
    label: "Quần",
    types: [
      { value: "jeans", label: "Quần jeans" },
      { value: "trouser", label: "Quần tây" },
      { value: "short", label: "Quần short" },
      { value: "jogger", label: "Quần jogger" },
      { value: "skirt", label: "Chân váy" },
      { value: "other", label: "Loại quần khác" },
    ],
  },
};

const SIZE_OPTIONS = ["S", "M", "L", "XL", "XXL"];
const COLOR_OPTIONS = [
  { value: "white", label: "Trắng" },
  { value: "black", label: "Đen" },
  { value: "blue", label: "Xanh dương" },
  { value: "green", label: "Xanh lá" },
  { value: "red", label: "Đỏ" },
  { value: "gray", label: "Xám" },
  { value: "brown", label: "Nâu" },
  { value: "beige", label: "Be" },
  { value: "pink", label: "Hồng" },
  { value: "yellow", label: "Vàng" },
  { value: "purple", label: "Tím" },
];
const SIZE_RANK = { S: 1, M: 2, L: 3, XL: 4, XXL: 5 };

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
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = emptyText;
  placeholder.disabled = options.length > 0;
  placeholder.selected = true;
  selectEl.appendChild(placeholder);

  if (options.length === 0) {
    return;
  }

  options.forEach((entry) => {
    const option = document.createElement("option");
    option.value = String(entry.value);
    option.textContent = entry.label;
    selectEl.appendChild(option);
  });
}

function composeCategory(group, type) {
  return `${group}:${type}`;
}

function splitCategory(rawCategory) {
  const raw = String(rawCategory || "").trim().toLowerCase();
  if (!raw) {
    return { group: "shirt", type: "other" };
  }

  const separators = [":", "/", "-"];
  for (const sep of separators) {
    if (raw.includes(sep)) {
      const [left, right] = raw.split(sep, 2);
      return {
        group: CATEGORY_TREE[left] ? left : "shirt",
        type: right || "other",
      };
    }
  }

  if (raw.includes("pant") || raw.includes("quan") || raw.includes("jean")) {
    return { group: "pants", type: "other" };
  }
  return { group: "shirt", type: "other" };
}

function syncCategoryTypeOptions() {
  const group = categoryGroupSelect.value || "shirt";
  const types = CATEGORY_TREE[group] ? CATEGORY_TREE[group].types : CATEGORY_TREE.shirt.types;
  const current = categoryTypeSelect.value;

  fillSelect(
    categoryTypeSelect,
    types.map((t) => ({ value: t.value, label: t.label })),
    "Chọn loại đồ",
  );

  if (types.some((t) => t.value === current)) {
    categoryTypeSelect.value = current;
  } else if (types.length > 0) {
    categoryTypeSelect.value = types[0].value;
  }
}

function initializeDropdowns() {
  fillSelect(
    categoryGroupSelect,
    Object.entries(CATEGORY_TREE).map(([value, config]) => ({ value, label: config.label })),
    "Chọn nhóm đồ",
  );

  categoryGroupSelect.value = "shirt";
  syncCategoryTypeOptions();

  fillSelect(sizeSelect, SIZE_OPTIONS.map((s) => ({ value: s, label: s })), "Chọn size");
  fillSelect(colorSelect, COLOR_OPTIONS, "Chọn màu");

  categoryTypeSelect.value = "tshirt";
  sizeSelect.value = "M";
  colorSelect.value = "blue";
}

function setClothingInputState(isExistingMode) {
  categoryGroupSelect.disabled = isExistingMode;
  categoryTypeSelect.disabled = isExistingMode;
  sizeSelect.disabled = isExistingMode;
  colorSelect.disabled = isExistingMode;
  clothingFileInput.disabled = isExistingMode;
}

function applyClothingToFields(item) {
  if (!item) {
    return;
  }

  const parsed = splitCategory(item.category);
  categoryGroupSelect.value = CATEGORY_TREE[parsed.group] ? parsed.group : "shirt";
  syncCategoryTypeOptions();

  if (Array.from(categoryTypeSelect.options).some((opt) => opt.value === parsed.type)) {
    categoryTypeSelect.value = parsed.type;
  } else {
    categoryTypeSelect.value = "other";
  }

  if (SIZE_OPTIONS.includes(String(item.size_label || "").toUpperCase())) {
    sizeSelect.value = String(item.size_label).toUpperCase();
  }

  const normalizedColor = String(item.color || "").toLowerCase();
  if (COLOR_OPTIONS.some((entry) => entry.value === normalizedColor)) {
    colorSelect.value = normalizedColor;
  }

  imagePathPreviewInput.value = item.image_path || "";
}

function syncModeVisibility() {
  const userMode = selectedMode("user_mode");
  const clothingMode = selectedMode("clothing_mode");
  const isExistingClothing = clothingMode === "existing";
  existingUserGroup.style.display = userMode === "existing" ? "grid" : "none";
  existingClothingGroup.style.display = isExistingClothing ? "grid" : "none";
  setClothingInputState(isExistingClothing);

  if (isExistingClothing) {
    const selectedId = Number(existingClothingSelect.value);
    const item = clothingCache.find((c) => c.id === selectedId);
    applyClothingToFields(item);
  } else {
    imagePathPreviewInput.value = "";
    clothingFileInput.value = "";
  }
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
    "Không có user. Chuyển sang tạo user mới.",
  );
}

async function loadClothing() {
  clothingCache = await apiJson("/clothing-items?limit=500", { method: "GET" });
  fillSelect(
    existingClothingSelect,
    clothingCache.map((c) => ({
      value: c.id,
      label: `#${c.id} - user ${c.user_id} - ${c.category} - ${String(c.size_label).toUpperCase()} - ${c.color}`,
    })),
    "Không có clothing item. Chuyển sang tạo item mới.",
  );

  if (clothingCache.length > 0) {
    existingClothingSelect.value = String(clothingCache[0].id);
    applyClothingToFields(clothingCache[0]);
  } else {
    imagePathPreviewInput.value = "";
  }
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
    if (!item) {
      throw new Error("Selected clothing item was not found in the current catalog");
    }

    applyClothingToFields(item);
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
    category: composeCategory(categoryGroupSelect.value, categoryTypeSelect.value),
    size_label: sizeSelect.value,
    color: colorSelect.value,
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
  applyClothingToFields(cloth);
  return cloth.id;
}

function estimateSizeFromMeasurement(measurement) {
  const chest = Number(measurement && measurement.chest_cm);
  if (!Number.isFinite(chest)) {
    return "M";
  }
  if (chest < 90) return "S";
  if (chest < 98) return "M";
  if (chest < 106) return "L";
  if (chest < 114) return "XL";
  return "XXL";
}

async function autoPickClothing() {
  const userId = Number(existingUserSelect.value);
  if (!Number.isFinite(userId) || userId <= 0) {
    throw new Error("Please select an existing user before auto-pick");
  }

  if (clothingCache.length === 0) {
    throw new Error("No clothing items available for selected user");
  }

  let targetSize = "M";
  try {
    const measurement = await apiJson(`/body-measurements/latest/${userId}`, { method: "GET" });
    targetSize = estimateSizeFromMeasurement(measurement);
    log(`Auto-pick target size from latest body data: ${targetSize}`);
  } catch (_error) {
    log("Auto-pick uses default target size M (no latest body measurement found).");
  }

  const withRank = clothingCache
    .map((item) => {
      const rank = SIZE_RANK[String(item.size_label || "").toUpperCase()] || SIZE_RANK.M;
      const targetRank = SIZE_RANK[targetSize] || SIZE_RANK.M;
      return { item, distance: Math.abs(rank - targetRank) };
    })
    .sort((a, b) => a.distance - b.distance);

  const picked = withRank[0].item;
  existingClothingSelect.value = String(picked.id);
  applyClothingToFields(picked);
  log(`Auto-picked clothing item id=${picked.id}, size=${String(picked.size_label).toUpperCase()}`);
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

categoryGroupSelect.addEventListener("change", () => {
  syncCategoryTypeOptions();
});

existingClothingSelect.addEventListener("change", () => {
  const selectedId = Number(existingClothingSelect.value);
  const item = clothingCache.find((c) => c.id === selectedId);
  applyClothingToFields(item);
});

existingUserSelect.addEventListener("change", async () => {
  try {
    log(`Selected existing user #${existingUserSelect.value}. Clothing catalog remains global across all users.`);
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

autoPickClothingBtn.addEventListener("click", async () => {
  try {
    await autoPickClothing();
  } catch (error) {
    log(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
});

async function initialize() {
  initializeDropdowns();
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

