using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class TaskStatusResponse
{
    public string task_id;
    public string status; // "pending", "processing", "completed", "failed"
    public string output_url;
    public string message;
}

[System.Serializable]
public class UserListItem
{
    public int id;
    public string name;
    public string gender;
}

[System.Serializable]
public class ClothingListItem
{
    public int id;
    public string display_name;
    public string size_label;
    public string color;
    public string slot;
}

[System.Serializable]
public class JsonArrayWrapper<T> { public T[] Items; }

[System.Serializable]
public enum AvatarGender
{
    Male,
    Female,
}

public class VRBackendClient : MonoBehaviour
{
    [Header("Backend Settings")]
    public string backendUrl = "http://localhost:8000";
    public bool autoHealthCheckOnStart = true;

    [Header("Gender Selection")]
    public AvatarGender selectedGender = AvatarGender.Male;

    [Header("User Selection")]
    public int selectedUserId = -1;
    public int selectedClothingId = -1;

    [Header("UI References")]
    public RemyWardrobeViewer wardrobeViewer;

    [Header("Overlay UI")]
    public bool showOverlay = true;
    public Vector2 overlayPosition = new Vector2(20f, 20f);
    public float overlayWidth = 500f;
    public float overlayHeight = 640f;

    [Header("Avatar Target")]
    [Tooltip("Kéo thả Mesh của cái Áo (Tops) vào đây")]
    public Renderer clothingRenderer;
    [Tooltip("Kéo thả Mesh của cái Quần (Bottoms) vào đây")]
    public Renderer pantsRenderer;

    [Header("Optional Helpers")]
    public Transform avatarRoot;       // Nếu có model cha, script sẽ tự tìm renderer trong nhánh này.

    private UserListItem[] _userList;
    private ClothingListItem[] _clothingList;
    private RemyWardrobeViewer[] _allWardrobeViewers;
    private Vector2 _userScroll;
    private Vector2 _clothingScroll;
    private GUIStyle _titleStyle;
    private GUIStyle _sectionStyle;
    private GUIStyle _itemButtonStyle;
    bool _isWorkflowRunning;

    void Reset()
    {
        TryAutoAssignAvatarRenderer();
    }

    void OnValidate()
    {
        if (clothingRenderer == null && pantsRenderer == null)
        {
            TryAutoAssignAvatarRenderer();
        }
    }

    private void EnsureWardrobeViewerReference()
    {
        CacheWardrobeViewers();
        if (_allWardrobeViewers != null && _allWardrobeViewers.Length > 0)
        {
            wardrobeViewer = ResolveWardrobeViewerForGender();
        }

        if (wardrobeViewer == null)
        {
            wardrobeViewer = FindFirstObjectByType<RemyWardrobeViewer>();
        }
    }

    private void CacheWardrobeViewers()
    {
        if (_allWardrobeViewers != null && _allWardrobeViewers.Length > 0)
        {
            return;
        }

        _allWardrobeViewers = FindObjectsByType<RemyWardrobeViewer>(FindObjectsInactive.Include, FindObjectsSortMode.None);
    }

    private RemyWardrobeViewer ResolveWardrobeViewerForGender()
    {
        if (_allWardrobeViewers == null || _allWardrobeViewers.Length == 0)
        {
            return null;
        }

        RemyWardrobeViewer fallback = _allWardrobeViewers[0];
        string desiredName = selectedGender == AvatarGender.Female ? "megan" : "remy";

        for (int i = 0; i < _allWardrobeViewers.Length; i++)
        {
            RemyWardrobeViewer viewer = _allWardrobeViewers[i];
            if (viewer == null)
            {
                continue;
            }

            viewer.autoFetchCatalogOnStart = false;

            string objectName = viewer.gameObject.name.ToLowerInvariant();
            string rootName = viewer.avatarRoot != null ? viewer.avatarRoot.name.ToLowerInvariant() : string.Empty;
            if (objectName.Contains(desiredName) || rootName.Contains(desiredName))
            {
                return viewer;
            }
        }

        return fallback;
    }

    private void ApplySelectedGender()
    {
        CacheWardrobeViewers();
        if (_allWardrobeViewers == null || _allWardrobeViewers.Length == 0)
        {
            return;
        }

        RemyWardrobeViewer activeViewer = ResolveWardrobeViewerForGender();
        wardrobeViewer = activeViewer;

        for (int i = 0; i < _allWardrobeViewers.Length; i++)
        {
            RemyWardrobeViewer viewer = _allWardrobeViewers[i];
            if (viewer == null)
            {
                continue;
            }

            viewer.autoFetchCatalogOnStart = false;
            bool shouldBeActive = viewer == activeViewer;
            if (viewer.gameObject.activeSelf != shouldBeActive)
            {
                viewer.gameObject.SetActive(shouldBeActive);
            }
        }

        ApplyUserFilterToWardrobe();
    }

    private void ApplyUserFilterToWardrobe()
    {
        EnsureWardrobeViewerReference();
        if (wardrobeViewer == null)
        {
            Debug.LogWarning("Khong tim thay RemyWardrobeViewer de dong bo user filter.");
            return;
        }

        wardrobeViewer.optionalUserIdFilter = selectedUserId;
        wardrobeViewer.RefreshCatalog();
    }

    private void EnsureGuiStyles()
    {
        if (_titleStyle != null)
        {
            return;
        }

        _titleStyle = new GUIStyle(GUI.skin.label);
        _titleStyle.fontSize = 20;
        _titleStyle.fontStyle = FontStyle.Bold;

        _sectionStyle = new GUIStyle(GUI.skin.label);
        _sectionStyle.fontSize = 16;
        _sectionStyle.fontStyle = FontStyle.Bold;

        _itemButtonStyle = new GUIStyle(GUI.skin.button);
        _itemButtonStyle.fontSize = 14;
        _itemButtonStyle.alignment = TextAnchor.MiddleLeft;
        _itemButtonStyle.padding = new RectOffset(10, 10, 8, 8);
    }

    private string GetGenderLabel(AvatarGender gender)
    {
        return gender == AvatarGender.Female ? "Nu" : "Nam";
    }

    private bool MatchesSelectedGender(UserListItem user)
    {
        if (user == null)
        {
            return false;
        }

        string normalized = string.IsNullOrWhiteSpace(user.gender)
            ? "male"
            : user.gender.ToLowerInvariant();
        bool isFemale = normalized == "female";
        return selectedGender == AvatarGender.Female ? isFemale : !isFemale;
    }

    private List<UserListItem> GetVisibleUsers()
    {
        List<UserListItem> result = new List<UserListItem>();
        if (_userList == null || _userList.Length == 0)
        {
            return result;
        }

        for (int i = 0; i < _userList.Length; i++)
        {
            UserListItem user = _userList[i];
            if (MatchesSelectedGender(user))
            {
                result.Add(user);
            }
        }

        // Ban ghi moi nhat len dau danh sach.
        result.Sort((a, b) => b.id.CompareTo(a.id));
        return result;
    }

    private bool EnsureUserSelectionMatchesCurrentGender()
    {
        List<UserListItem> visibleUsers = GetVisibleUsers();
        if (visibleUsers.Count == 0)
        {
            selectedUserId = -1;
            selectedClothingId = -1;
            _clothingList = new ClothingListItem[0];
            ApplyUserFilterToWardrobe();
            return false;
        }

        bool selectedStillVisible = false;
        for (int i = 0; i < visibleUsers.Count; i++)
        {
            if (visibleUsers[i].id == selectedUserId)
            {
                selectedStillVisible = true;
                break;
            }
        }

        if (!selectedStillVisible)
        {
            selectedUserId = visibleUsers[0].id;
            selectedClothingId = -1;
            ApplyUserFilterToWardrobe();
            return true;
        }

        ApplyUserFilterToWardrobe();
        return false;
    }

    private string BuildUserLabel(UserListItem user)
    {
        string userName = user != null ? user.name : string.Empty;
        string genderLabel = "Nam";
        if (user != null && !string.IsNullOrWhiteSpace(user.gender) && user.gender.ToLowerInvariant() == "female")
        {
            genderLabel = "Nu";
        }

        if (string.IsNullOrWhiteSpace(userName))
        {
            return "User #" + (user != null ? user.id.ToString() : "?") + " (" + genderLabel + ")";
        }

        return userName + "  (#" + user.id + ", " + genderLabel + ")";
    }

    private void SyncGenderFromUser(UserListItem user)
    {
        if (user == null || string.IsNullOrWhiteSpace(user.gender))
        {
            return;
        }

        string normalized = user.gender.ToLowerInvariant();
        AvatarGender newGender = normalized == "female" ? AvatarGender.Female : AvatarGender.Male;
        if (newGender != selectedGender)
        {
            selectedGender = newGender;
            ApplySelectedGender();
        }
    }

    private string BuildClothingLabel(ClothingListItem item)
    {
        if (item == null)
        {
            return "Item #?";
        }

        string name = string.IsNullOrWhiteSpace(item.display_name) ? "Item #" + item.id : item.display_name;
        string size = string.IsNullOrWhiteSpace(item.size_label) ? "-" : item.size_label;
        string color = string.IsNullOrWhiteSpace(item.color) ? "-" : item.color;
        return name + " | Size " + size + " | Mau " + color;
    }

    private Rect ResolveOverlayRect()
    {
        float x = overlayPosition.x;
        float y = overlayPosition.y;

        EnsureWardrobeViewerReference();
        if (wardrobeViewer != null && wardrobeViewer.showOverlay)
        {
            Rect remyRect = new Rect(
                wardrobeViewer.overlayPosition.x,
                wardrobeViewer.overlayPosition.y,
                wardrobeViewer.overlayWidth,
                wardrobeViewer.overlayHeight
            );
            Rect currentRect = new Rect(x, y, overlayWidth, overlayHeight);

            if (currentRect.Overlaps(remyRect))
            {
                x = remyRect.xMax + 20f;
            }
        }

        float maxX = Mathf.Max(0f, Screen.width - overlayWidth - 12f);
        x = Mathf.Clamp(x, 12f, maxX);
        y = Mathf.Max(12f, y);
        return new Rect(x, y, overlayWidth, overlayHeight);
    }

    void Awake()
    {
        EnsureWardrobeViewerReference();
        ApplySelectedGender();
    }

    void Start()
    {
        if (clothingRenderer == null && pantsRenderer == null)
        {
            TryAutoAssignAvatarRenderer();
        }

        EnsureWardrobeViewerReference();

        Debug.Log("🔌 Khởi động VR Client...");

        if (autoHealthCheckOnStart)
        {
            StartCoroutine(TestHealthCheck());
        }

        // Fetch danh sách user khi khởi động
        StartCoroutine(FetchUserList());

        if (selectedUserId > 0)
        {
            ApplyUserFilterToWardrobe();
            StartCoroutine(FetchClothingByUser(selectedUserId));
        }
    }

    void OnGUI()
    {
        if (!showOverlay)
        {
            return;
        }

        EnsureGuiStyles();

        Rect overlayRect = ResolveOverlayRect();
        GUILayout.BeginArea(overlayRect, GUI.skin.box);
        GUILayout.Label("VR Backend Client", _titleStyle);

        GUILayout.Space(6f);
        GUILayout.Label("Gioi tinh:", _sectionStyle);
        GUILayout.BeginHorizontal();
        if (GUILayout.Toggle(selectedGender == AvatarGender.Male, "Nam", GUI.skin.button, GUILayout.Height(34f)))
        {
            if (selectedGender != AvatarGender.Male)
            {
                selectedGender = AvatarGender.Male;
                ApplySelectedGender();
                bool changedUser = EnsureUserSelectionMatchesCurrentGender();
                if (changedUser && selectedUserId > 0)
                {
                    StartCoroutine(FetchClothingByUser(selectedUserId));
                }
            }
        }

        if (GUILayout.Toggle(selectedGender == AvatarGender.Female, "Nu", GUI.skin.button, GUILayout.Height(34f)))
        {
            if (selectedGender != AvatarGender.Female)
            {
                selectedGender = AvatarGender.Female;
                ApplySelectedGender();
                bool changedUser = EnsureUserSelectionMatchesCurrentGender();
                if (changedUser && selectedUserId > 0)
                {
                    StartCoroutine(FetchClothingByUser(selectedUserId));
                }
            }
        }
        GUILayout.EndHorizontal();

        GUILayout.Space(8f);
        GUILayout.Label("Chon User:", _sectionStyle);

        List<UserListItem> visibleUsers = GetVisibleUsers();
        if (visibleUsers.Count > 0)
        {
            _userScroll = GUILayout.BeginScrollView(_userScroll, GUILayout.Height(220f));
            for (int i = 0; i < visibleUsers.Count; i++)
            {
                UserListItem user = visibleUsers[i];
                bool isSelected = user != null && user.id == selectedUserId;
                Color oldColor = GUI.backgroundColor;
                if (isSelected)
                {
                    GUI.backgroundColor = new Color(0.45f, 0.68f, 0.95f, 1f);
                }

                if (GUILayout.Button(BuildUserLabel(user), _itemButtonStyle, GUILayout.Height(40f)))
                {
                    if (user != null && selectedUserId != user.id)
                    {
                        selectedUserId = user.id;
                        selectedClothingId = -1;
                        SyncGenderFromUser(user);
                        ApplyUserFilterToWardrobe();
                        StartCoroutine(FetchClothingByUser(selectedUserId));
                    }
                }

                GUI.backgroundColor = oldColor;
                GUILayout.Space(4f);
            }
            GUILayout.EndScrollView();
        }
        else
        {
            if (_userList == null)
            {
                GUILayout.Label("Dang tai danh sach user...");
            }
            else
            {
                GUILayout.Label("Khong co user phu hop voi gioi tinh dang chon.");
            }
        }

        GUILayout.Space(10f);
        GUILayout.Label("Quan ao theo user da chon:", _sectionStyle);

        if (selectedUserId > 0)
        {
            if (_clothingList != null && _clothingList.Length > 0)
            {
                _clothingScroll = GUILayout.BeginScrollView(_clothingScroll, GUILayout.Height(250f));
                for (int i = 0; i < _clothingList.Length; i++)
                {
                    ClothingListItem cloth = _clothingList[i];
                    bool isSelected = cloth != null && cloth.id == selectedClothingId;
                    Color oldColor = GUI.backgroundColor;
                    if (isSelected)
                    {
                        GUI.backgroundColor = new Color(0.54f, 0.86f, 0.64f, 1f);
                    }

                    if (GUILayout.Button(BuildClothingLabel(cloth), _itemButtonStyle, GUILayout.Height(44f)))
                    {
                        if (cloth != null)
                        {
                            selectedClothingId = cloth.id;
                        }
                    }

                    GUI.backgroundColor = oldColor;
                    GUILayout.Space(4f);
                }
                GUILayout.EndScrollView();
            }
            else
            {
                GUILayout.Label("User nay khong co quan ao.");
            }

            GUILayout.Space(10f);
            if (GUILayout.Button("Chay Fitting Workflow", GUILayout.Height(48f)))
            {
                if (selectedClothingId > 0)
                {
                    RunFittingWorkflow();
                }
                else
                {
                    Debug.LogWarning("Vui long chon 1 mon quan ao truoc.");
                }
            }
        }
        else
        {
            GUILayout.Label("Hay chon user de hien thi danh sach quan ao.");
        }

        GUILayout.EndArea();
    }

    public void TryAutoAssignAvatarRenderer()
    {
        Renderer[] candidateRenderers = avatarRoot != null
            ? avatarRoot.GetComponentsInChildren<Renderer>(true)
            : FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None);

        if (candidateRenderers == null || candidateRenderers.Length == 0)
        {
            return;
        }

        if (clothingRenderer == null)
        {
            clothingRenderer = candidateRenderers[0];
            Debug.Log($"<color=cyan>🔎 Tự gán clothingRenderer: {clothingRenderer.name}</color>");
        }

        if (pantsRenderer == null && candidateRenderers.Length > 1)
        {
            pantsRenderer = candidateRenderers[1];
            Debug.Log($"<color=cyan>🔎 Tự gán pantsRenderer: {pantsRenderer.name}</color>");
        }
    }

    public void StartHealthCheck()
    {
        StartCoroutine(TestHealthCheck());
    }

    // ... (Giữ nguyên các hàm check và API khác, chỉ sửa reference apply hình ảnh)
    // Tự động rút gọn code bằng cách bỏ qua các hàm ko đổi ở đây...

    // (Tôi sẽ thay đổi toàn cục bên dưới)

    IEnumerator TestHealthCheck()
    {
        using (UnityWebRequest request = UnityWebRequest.Get(backendUrl + "/health"))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log("<color=green>✅ Đã kết nối với Backend: " + request.downloadHandler.text + "</color>");
            }
            else
            {
                Debug.LogError("<color=red>🛑 Lỗi kết nối: " + request.error + "</color>");
                Debug.LogWarning("Kiểm tra xem Tùng/Niên đã bật Backend chạy ở cổng 8000 chưa (uvicorn main:app --port 8000)");
            }
        }
    }

    // 💡 Điểm ăn tiền: Bạn nhấp chuột phải vào script này ở Inspector sẽ thấy nút "Test Request Fitting"
    [ContextMenu("Test Request Fitting")]
    public void RunFittingWorkflow()
    {
        if (_isWorkflowRunning)
        {
            Debug.LogWarning("⏳ Đang có workflow chạy rồi, chờ xíu nha.");
            return;
        }

        if (selectedUserId == -1 || selectedClothingId == -1)
        {
            Debug.LogError("❌ Vui lòng chọn User và Quần Áo từ UI.");
            return;
        }

        StartCoroutine(ExecuteFittingWorkflow(selectedUserId, selectedClothingId));
    }

    [ContextMenu("Test Pose Sync (Image -> Rig)")]
    public void TestPoseSync()
    {
        VRPoseSyncClient poseSync = GetComponent<VRPoseSyncClient>();
        if (poseSync == null)
        {
            Debug.LogWarning("Chưa gắn VRPoseSyncClient trên GameObject này.");
            return;
        }

        poseSync.EstimatePoseAndApplyToRig();
    }

    IEnumerator FetchUserList()
    {
        Debug.Log("🔍 Đang tải danh sách User từ Database...");
        using (UnityWebRequest req = UnityWebRequest.Get(backendUrl + "/users"))
        {
            yield return req.SendWebRequest();
            if (req.result == UnityWebRequest.Result.Success)
            {
                string json = "{\"Items\":" + req.downloadHandler.text + "}";
                var wrapper = JsonUtility.FromJson<JsonArrayWrapper<UserListItem>>(json);
                if (wrapper != null && wrapper.Items.Length > 0)
                {
                    _userList = wrapper.Items;
                    Debug.Log($"<color=green>✅ Tải được {_userList.Length} users.</color>");
                    EnsureUserSelectionMatchesCurrentGender();

                    if (selectedUserId > 0)
                    {
                        StartCoroutine(FetchClothingByUser(selectedUserId));
                    }
                }
                else
                {
                    _userList = new UserListItem[0];
                }
            }
            else
            {
                Debug.LogError("❌ Lỗi tải danh sách user: " + req.error);
            }
        }
    }

    IEnumerator FetchClothingByUser(int userId)
    {
        Debug.Log($"🔍 Đang tải quần áo của User {userId}...");
        using (UnityWebRequest req = UnityWebRequest.Get($"{backendUrl}/clothing-items?limit=500&user_id={userId}"))
        {
            yield return req.SendWebRequest();
            if (req.result == UnityWebRequest.Result.Success)
            {
                string json = "{\"Items\":" + req.downloadHandler.text + "}";
                var wrapper = JsonUtility.FromJson<JsonArrayWrapper<ClothingListItem>>(json);
                if (wrapper != null && wrapper.Items.Length > 0)
                {
                    _clothingList = wrapper.Items;
                    Debug.Log($"<color=green>✅ Tải được {_clothingList.Length} quần áo.</color>");

                    bool hasCurrentSelection = false;
                    for (int i = 0; i < _clothingList.Length; i++)
                    {
                        if (_clothingList[i] != null && _clothingList[i].id == selectedClothingId)
                        {
                            hasCurrentSelection = true;
                            break;
                        }
                    }

                    if (!hasCurrentSelection)
                    {
                        selectedClothingId = _clothingList[0].id;
                    }
                }
                else
                {
                    _clothingList = new ClothingListItem[0];
                    selectedClothingId = -1;
                    Debug.LogWarning($"⚠️ User {userId} không có quần áo nào.");
                }
            }
            else
            {
                Debug.LogError("❌ Lỗi tải quần áo: " + req.error);
            }
        }
    }

    IEnumerator ExecuteFittingWorkflow(int userId, int clothingId)
    {
        _isWorkflowRunning = true;
        Debug.Log($"🔄 Đang gửi yêu cầu Fitting (User {userId}, Quần áo {clothingId})...");

        string jsonPayload = $"{{\"user_id\": {userId}, \"clothing_item_id\": {clothingId}}}";

        using (UnityWebRequest request = new UnityWebRequest(backendUrl + "/tasks/generate-texture", "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonPayload);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("❌ Lỗi gọi API: " + request.error);
                _isWorkflowRunning = false;
                yield break;
            }

            TaskStatusResponse response = JsonUtility.FromJson<TaskStatusResponse>(request.downloadHandler.text);
            if (response == null || string.IsNullOrEmpty(response.task_id))
            {
                Debug.LogError("❌ Backend trả dữ liệu task không hợp lệ.");
                _isWorkflowRunning = false;
                yield break;
            }

            string taskId = response.task_id;
            Debug.Log($"<color=yellow>⏳ Đã tạo Task (ID: {taskId}). Chờ AI backend tạo Texture...</color>");

            StartCoroutine(PollTaskStatus(taskId));
        }
    }

    IEnumerator PollTaskStatus(string taskId)
    {
        bool isDone = false;
        string resultUrl = "";

        while (!isDone)
        {
            yield return new WaitForSeconds(2.0f); // Polling mỗi 2 giây để đỡ quá tải backend

            using (UnityWebRequest request = UnityWebRequest.Get($"{backendUrl}/status/{taskId}"))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    TaskStatusResponse status = JsonUtility.FromJson<TaskStatusResponse>(request.downloadHandler.text);
                    Debug.Log($"[Task: {taskId}] Status: {status.status}");

                    if (status.status == "completed")
                    {
                        isDone = true;
                        resultUrl = status.output_url;
                    }
                    else if (status.status == "failed")
                    {
                        Debug.LogError("❌ AI Backend phản hồi thất bại: " + status.message);
                        _isWorkflowRunning = false;
                        yield break;
                    }
                }
                else
                {
                    Debug.LogError("Lỗi Polling: " + request.error);
                    _isWorkflowRunning = false;
                    yield break;
                }
            }
        }

        Debug.Log($"<color=green>🎉 AI chạy xong! Đang tải Skin mới: {resultUrl}...</color>");
        StartCoroutine(DownloadAndApplyTexture(resultUrl));
    }

    IEnumerator DownloadAndApplyTexture(string resultUrl)
    {
        if (string.IsNullOrEmpty(resultUrl))
        {
            Debug.LogError("❌ Backend không trả về đường dẫn texture.");
            _isWorkflowRunning = false;
            yield break;
        }

        string fullUrl = backendUrl + resultUrl; // Endpoint URL tải file hình trả về (ex: localhost:8000/textures/123.jpg)

        using (UnityWebRequest request = UnityWebRequestTexture.GetTexture(fullUrl))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Texture2D texture = DownloadHandlerTexture.GetContent(request);
                ApplyTextureToAvatar(texture);
            }
            else
            {
                Debug.LogError("❌ Failed to download texture: " + request.error);
            }
        }

        _isWorkflowRunning = false;
    }

    void ApplyTextureToAvatar(Texture2D texture)
    {
        bool applied = false;

        if (clothingRenderer != null)
        {
            ApplyToSingleRenderer(clothingRenderer, texture);
            applied = true;
        }

        if (pantsRenderer != null)
        {
            ApplyToSingleRenderer(pantsRenderer, texture);
            applied = true;
        }

        if (applied)
        {
            Debug.Log("<color=cyan>✨ Tada! Đã thay đồ thành công lên Mesh Quần Áo!</color>");
        }
        else
        {
            Debug.LogWarning("Chưa kéo thả Renderer của Áo/Quần vào Inspector nha, nhưng đã tải xong tải Texture.");
        }
    }

    void ApplyToSingleRenderer(Renderer rend, Texture2D tex)
    {
        Material mat = rend.material;
        mat.mainTexture = tex;
        if (mat.HasProperty("_BaseMap")) mat.SetTexture("_BaseMap", tex);
        if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", Color.white);
        if (mat.HasProperty("_Color")) mat.SetColor("_Color", Color.white);
    }
}
