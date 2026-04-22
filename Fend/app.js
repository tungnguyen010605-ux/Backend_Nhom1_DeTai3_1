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
const startCameraBtn = document.getElementById("start-camera-btn");
const stopCameraBtn = document.getElementById("stop-camera-btn");
const capturePoseBtn = document.getElementById("capture-pose-btn");
const poseVideo = document.getElementById("pose-video");
const poseCanvas = document.getElementById("pose-canvas");
const poseStatus = document.getElementById("pose-status");
const poseSummary = document.getElementById("pose-summary");

const categoryGroupSelect = document.getElementById("category-group-select");
const categoryTypeSelect = document.getElementById("category-type-select");
const sizeSelect = document.getElementById("size-select");
const colorSelect = document.getElementById("color-select");
const displayNameInput = document.getElementById("display-name-input");
const runtimeSlotSelect = document.getElementById("runtime-slot-select");
const renderModeSelect = document.getElementById("render-mode-select");
const modelPathInput = document.getElementById("model-path-input");
const bodyCompatibilityInput = document.getElementById("body-compatibility-input");
const runtimeNotesInput = document.getElementById("runtime-notes-input");
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
const RUNTIME_SLOT_OPTIONS = [
  { value: "top", label: "Top / Áo" },
  { value: "bottom", label: "Bottom / Quần" },
  { value: "shoes", label: "Shoes / Giày" },
  { value: "fullbody", label: "Full body" },
  { value: "accessory", label: "Accessory" },
];
const RENDER_MODE_OPTIONS = [
  { value: "texture", label: "Texture overlay" },
  { value: "prefab", label: "Prefab / outfit 3D" },
];
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
let activeCameraStream = null;
let latestPoseEstimate = null;

const measurementInputs = {
  name: form.querySelector('input[name="name"]'),
  height_cm: form.querySelector('input[name="height_cm"]'),
  chest_cm: form.querySelector('input[name="chest_cm"]'),
  waist_cm: form.querySelector('input[name="waist_cm"]'),
  hip_cm: form.querySelector('input[name="hip_cm"]'),
  inseam_cm: form.querySelector('input[name="inseam_cm"]'),
};

function log(message) {
  statusLog.textContent += `\n${message}`;
}

function resetUi() {
  statusLog.textContent = "Starting...";
  resultLink.textContent = "No result yet.";
  resultImage.style.display = "none";
  resultImage.removeAttribute("src");
}

function setPoseStatus(message) {
  poseStatus.textContent = message;
}

function updatePoseSummary(estimate) {
  if (!estimate) {
    poseSummary.textContent = "Chưa có keypoints.";
    return;
  }

  const m = estimate.measurements;
  poseSummary.textContent = [
    `Keypoints: ${estimate.keypoints.length}`,
    `Height: ${m.height_cm} cm`,
    `Chest: ${m.chest_cm} cm`,
    `Waist: ${m.waist_cm} cm`,
    `Hip: ${m.hip_cm} cm`,
    `Inseam: ${m.inseam_cm} cm`,
    `Shoulder: ${m.shoulder_cm} cm`,
    `Arm length: ${m.arm_length_cm} cm`,
  ].join("\n");
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
  fillSelect(runtimeSlotSelect, RUNTIME_SLOT_OPTIONS, "Chọn slot");
  fillSelect(renderModeSelect, RENDER_MODE_OPTIONS, "Chọn mode render");

  categoryTypeSelect.value = "tshirt";
  runtimeSlotSelect.value = "top";
  sizeSelect.value = "M";
  colorSelect.value = "blue";
  renderModeSelect.value = "texture";
}

function fillUserMeasurementFields(user) {
  if (!user) {
    return;
  }
  measurementInputs.name.value = user.name || "";
  measurementInputs.height_cm.value = user.height_cm ?? "";
  measurementInputs.chest_cm.value = user.chest_cm ?? "";
  measurementInputs.waist_cm.value = user.waist_cm ?? "";
  measurementInputs.hip_cm.value = user.hip_cm ?? "";
  measurementInputs.inseam_cm.value = user.inseam_cm ?? "";
}

function setClothingInputState(isExistingMode) {
  displayNameInput.disabled = isExistingMode;
  categoryGroupSelect.disabled = isExistingMode;
  categoryTypeSelect.disabled = isExistingMode;
  runtimeSlotSelect.disabled = isExistingMode;
  sizeSelect.disabled = isExistingMode;
  colorSelect.disabled = isExistingMode;
  renderModeSelect.disabled = isExistingMode;
  modelPathInput.disabled = isExistingMode;
  bodyCompatibilityInput.disabled = isExistingMode;
  runtimeNotesInput.disabled = isExistingMode;
  clothingFileInput.disabled = isExistingMode;
}

function parseBodyCompatibilityCsv(rawValue) {
  return String(rawValue || "")
    .split(",")
    .map((entry) => entry.trim().toLowerCase())
    .filter(Boolean);
}

function formatBodyCompatibility(value) {
  return Array.isArray(value) ? value.join(", ") : "";
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

  displayNameInput.value = item.display_name || "";

  const runtimeSlot = String(item.slot || "").toLowerCase();
  if (Array.from(runtimeSlotSelect.options).some((opt) => opt.value === runtimeSlot)) {
    runtimeSlotSelect.value = runtimeSlot;
  } else {
    runtimeSlotSelect.value = parsed.group === "pants" ? "bottom" : "top";
  }

  if (SIZE_OPTIONS.includes(String(item.size_label || "").toUpperCase())) {
    sizeSelect.value = String(item.size_label).toUpperCase();
  }

  const normalizedColor = String(item.color || "").toLowerCase();
  if (COLOR_OPTIONS.some((entry) => entry.value === normalizedColor)) {
    colorSelect.value = normalizedColor;
  }

  const renderMode = String(item.render_mode || "texture").toLowerCase();
  renderModeSelect.value = RENDER_MODE_OPTIONS.some((entry) => entry.value === renderMode)
    ? renderMode
    : "texture";
  modelPathInput.value = item.model_path || "";
  bodyCompatibilityInput.value = formatBodyCompatibility(item.body_compatibility);
  runtimeNotesInput.value = item.runtime_notes || "";
  imagePathPreviewInput.value = item.preview_image_path || item.image_path || "";
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
    displayNameInput.value = "";
    runtimeSlotSelect.value = "top";
    renderModeSelect.value = "texture";
    modelPathInput.value = "";
    bodyCompatibilityInput.value = "";
    runtimeNotesInput.value = "";
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

  if (usersCache.length > 0 && !existingUserSelect.value) {
    existingUserSelect.value = String(usersCache[0].id);
    fillUserMeasurementFields(usersCache[0]);
  }
}

async function loadClothing() {
  clothingCache = await apiJson("/clothing-items?limit=500", { method: "GET" });
  fillSelect(
    existingClothingSelect,
    clothingCache.map((c) => ({
      value: c.id,
      label: `#${c.id} - ${c.display_name || c.category} - ${String(c.render_mode || "texture").toUpperCase()} - ${String(c.size_label).toUpperCase()} - ${c.color}`,
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

function requireHeightReference() {
  const height = Number(measurementInputs.height_cm.value);
  if (!Number.isFinite(height) || height <= 50) {
    throw new Error("Hãy nhập chiều cao thật trước khi chụp pose");
  }
  return height;
}

async function startCamera() {
  if (activeCameraStream) {
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new Error("Trình duyệt hiện tại không hỗ trợ webcam");
  }

  activeCameraStream = await navigator.mediaDevices.getUserMedia({
    video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
    audio: false,
  });
  poseVideo.srcObject = activeCameraStream;
  await poseVideo.play();
  setPoseStatus("Camera đang bật. Đứng thẳng trong khung hình rồi bấm chụp pose.");
}

function stopCamera() {
  if (!activeCameraStream) {
    setPoseStatus("Camera đã tắt.");
    return;
  }
  activeCameraStream.getTracks().forEach((track) => track.stop());
  activeCameraStream = null;
  poseVideo.srcObject = null;
  setPoseStatus("Camera đã tắt.");
}

function applyPoseMeasurementsToForm(measurements) {
  measurementInputs.height_cm.value = measurements.height_cm;
  measurementInputs.chest_cm.value = measurements.chest_cm;
  measurementInputs.waist_cm.value = measurements.waist_cm;
  measurementInputs.hip_cm.value = measurements.hip_cm;
  measurementInputs.inseam_cm.value = measurements.inseam_cm;
}

async function capturePoseEstimate() {
  if (!activeCameraStream) {
    await startCamera();
  }

  const referenceHeight = requireHeightReference();
  const width = poseVideo.videoWidth || 640;
  const height = poseVideo.videoHeight || 480;

  poseCanvas.width = width;
  poseCanvas.height = height;
  const ctx = poseCanvas.getContext("2d");
  ctx.drawImage(poseVideo, 0, 0, width, height);

  const blob = await new Promise((resolve, reject) => {
    poseCanvas.toBlob((value) => {
      if (value) {
        resolve(value);
      } else {
        reject(new Error("Không thể tạo ảnh từ webcam"));
      }
    }, "image/jpeg", 0.92);
  });

  const payload = new FormData();
  payload.append("file", blob, "pose-capture.jpg");
  payload.append("reference_height_cm", String(referenceHeight));

  setPoseStatus("Đang gửi frame lên backend để ước lượng pose...");
  const estimate = await apiJson("/pose/estimate", {
    method: "POST",
    body: payload,
  });

  latestPoseEstimate = estimate;
  applyPoseMeasurementsToForm(estimate.measurements);
  updatePoseSummary(estimate);
  setPoseStatus("Đã nhận keypoints và tự điền số đo vào form.");
  log(`Pose estimated with ${estimate.keypoints.length} keypoints.`);
}

async function persistPoseMeasurementIfAvailable(userId, formData) {
  if (!latestPoseEstimate) {
    return;
  }

  const payload = {
    user_id: userId,
    height_cm: requireNumber(formData, "height_cm", "Please enter valid height"),
    chest_cm: requireNumber(formData, "chest_cm", "Please enter valid chest"),
    waist_cm: requireNumber(formData, "waist_cm", "Please enter valid waist"),
    hip_cm: requireNumber(formData, "hip_cm", "Please enter valid hip"),
    inseam_cm: requireNumber(formData, "inseam_cm", "Please enter valid inseam"),
    source: "mediapipe_ui",
    keypoints: latestPoseEstimate.keypoints,
  };

  log("2) Saving pose measurement to database...");
  await apiJson("/body-measurements", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  log("Pose measurement saved.");
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

  log("3) Preprocessing clothing image...");
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
    display_name: String(formData.get("display_name") || "").trim() || null,
    category: composeCategory(categoryGroupSelect.value, categoryTypeSelect.value),
    slot: runtimeSlotSelect.value || null,
    size_label: sizeSelect.value,
    color: colorSelect.value,
    image_path: preprocess.file_url,
    preview_image_path: preprocess.file_url,
    model_path: String(formData.get("model_path") || "").trim() || null,
    render_mode: renderModeSelect.value || "texture",
    body_compatibility: parseBodyCompatibilityCsv(formData.get("body_compatibility")),
    runtime_notes: String(formData.get("runtime_notes") || "").trim() || null,
  };

  log("4) Creating clothing item...");
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
    await persistPoseMeasurementIfAvailable(userId, formData);
    const clothingId = await resolveClothingId(formData, userId);

    log("5) Starting texture generation task...");
    const task = await apiJson("/tasks/generate-texture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, clothing_item_id: clothingId }),
    });

    log(`Task queued: task_id=${task.task_id}`);

    log("6) Polling task status...");
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
    const selectedId = Number(existingUserSelect.value);
    const user = usersCache.find((entry) => entry.id === selectedId);
    fillUserMeasurementFields(user);
    log(`Selected existing user #${existingUserSelect.value}. Clothing catalog remains global across all users.`);
  } catch (error) {
    log(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
});

startCameraBtn.addEventListener("click", async () => {
  try {
    await startCamera();
  } catch (error) {
    setPoseStatus(`Lỗi camera: ${error instanceof Error ? error.message : String(error)}`);
    log(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
});

stopCameraBtn.addEventListener("click", () => {
  stopCamera();
});

capturePoseBtn.addEventListener("click", async () => {
  try {
    await capturePoseEstimate();
  } catch (error) {
    setPoseStatus(`Lỗi pose: ${error instanceof Error ? error.message : String(error)}`);
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
    if (usersCache.length > 0) {
      fillUserMeasurementFields(usersCache[0]);
    }
  } catch (error) {
    log(`Error: ${error instanceof Error ? error.message : String(error)}`);
  }
}

initialize();

window.addEventListener("beforeunload", () => {
  stopCamera();
});
