using System.Collections;
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
public class TinyItem { public int id; }

[System.Serializable]
public class JsonArrayWrapper<T> { public T[] Items; }

public class VRBackendClient : MonoBehaviour
{
    [Header("Backend Settings")]
    public string backendUrl = "http://localhost:8000";
    public int testUserId = 1;         // Dùng ID giả để test
    public int testClothingId = 1;     // Dùng ID giả để test
    public bool autoHealthCheckOnStart = true;
    
    [Header("Avatar Target")]
    public Renderer avatarRenderer;    // Kéo thả phần thân Avatar vào đây để thay đồ.

    [Header("Optional Helpers")]
    public Transform avatarRoot;       // Nếu có model cha, script sẽ tự tìm renderer trong nhánh này.

    bool _isWorkflowRunning;

    void Reset()
    {
        TryAutoAssignAvatarRenderer();
    }

    void OnValidate()
    {
        if (avatarRenderer == null)
        {
            TryAutoAssignAvatarRenderer();
        }
    }

    void Start()
    {
        if (avatarRenderer == null)
        {
            TryAutoAssignAvatarRenderer();
        }

        Debug.Log("🔌 Khởi động VR Client...");

        if (autoHealthCheckOnStart)
        {
            StartCoroutine(TestHealthCheck());
        }
    }

    public void TryAutoAssignAvatarRenderer()
    {
        Renderer foundRenderer = null;

        if (avatarRoot != null)
        {
            foundRenderer = avatarRoot.GetComponentInChildren<SkinnedMeshRenderer>(true);
            if (foundRenderer == null)
            {
                foundRenderer = avatarRoot.GetComponentInChildren<MeshRenderer>(true);
            }
        }

        if (foundRenderer == null)
        {
            foundRenderer = FindFirstObjectByType<SkinnedMeshRenderer>(FindObjectsInactive.Include);
            if (foundRenderer == null)
            {
                foundRenderer = FindFirstObjectByType<MeshRenderer>(FindObjectsInactive.Include);
            }
        }

        if (foundRenderer != null)
        {
            avatarRenderer = foundRenderer;
            Debug.Log($"<color=cyan>🔎 Tự gán avatarRenderer thành công: {avatarRenderer.name}</color>");
        }
    }

    public void StartHealthCheck()
    {
        StartCoroutine(TestHealthCheck());
    }

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
    public void RunTestFittingWorkflow()
    {
        if (_isWorkflowRunning)
        {
            Debug.LogWarning("⏳ Đang có workflow chạy rồi, chờ xíu nha.");
            return;
        }

        StartCoroutine(ExecuteFittingWorkflow(testUserId, testClothingId));
    }

    // 🎲 Thưởng thêm: Tính năng tự động quét CSDL và lấy ID ngẫu nhiên!
    [ContextMenu("Test Random User & Cloth")]
    public void TestRandomFromDB()
    {
        if (_isWorkflowRunning)
        {
            Debug.LogWarning("⏳ Đang có workflow chạy rồi, chờ xíu nha.");
            return;
        }

        StartCoroutine(FetchRandomAndFit());
    }

    IEnumerator FetchRandomAndFit()
    {
        int pickedUser = -1;
        int pickedCloth = -1;

        Debug.Log("🔍 Đang tải danh sách User từ Database...");
        using (UnityWebRequest req = UnityWebRequest.Get(backendUrl + "/users"))
        {
            yield return req.SendWebRequest();
            if (req.result == UnityWebRequest.Result.Success)
            {
                string json = "{\"Items\":" + req.downloadHandler.text + "}";
                var users = JsonUtility.FromJson<JsonArrayWrapper<TinyItem>>(json);
                if (users != null && users.Items.Length > 0)
                {
                    pickedUser = users.Items[Random.Range(0, users.Items.Length)].id;
                }
            }
        }

        Debug.Log("🔍 Đang tải danh sách Clothing từ Database...");
        using (UnityWebRequest req = UnityWebRequest.Get(backendUrl + "/clothing-items"))
        {
            yield return req.SendWebRequest();
            if (req.result == UnityWebRequest.Result.Success)
            {
                string json = "{\"Items\":" + req.downloadHandler.text + "}";
                var clothes = JsonUtility.FromJson<JsonArrayWrapper<TinyItem>>(json);
                if (clothes != null && clothes.Items.Length > 0)
                {
                    pickedCloth = clothes.Items[Random.Range(0, clothes.Items.Length)].id;
                }
            }
        }

        if (pickedUser != -1 && pickedCloth != -1)
        {
            Debug.Log($"<color=green>🎲 BỐC THĂM THÀNH CÔNG: Chốt đơn User [{pickedUser}] mặc áo [{pickedCloth}]</color>");
            testUserId = pickedUser;
            testClothingId = pickedCloth;
            StartCoroutine(ExecuteFittingWorkflow(pickedUser, pickedCloth));
        }
        else
        {
            Debug.LogError("❌ Không lấy được dữ liệu. Bạn hãy vào http://localhost:8000/ui tạo vài cái đi nha.");
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
                
                if (avatarRenderer != null)
                {
                    // Ốp ảnh mới xuất từ AI vào skin của nhân vật
                    avatarRenderer.material.mainTexture = texture;
                    Debug.Log("<color=cyan>✨ Tada! Đã thay đồ thành công cho Avatar!</color>");
                }
                else
                {
                    Debug.LogWarning("Chưa kéo thả Renderer của avatar vào đoạn [Avatar Target] bên Inspector nha, nhưng đã tải xong tải Texture.");
                }
            }
            else
            {
                Debug.LogError("❌ Failed to download texture: " + request.error);
            }
        }

        _isWorkflowRunning = false;
    }
}
