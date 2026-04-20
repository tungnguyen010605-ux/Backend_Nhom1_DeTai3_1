using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class ClothingCatalogItem
{
    public int id;
    public int user_id;
    public string category;
    public string size_label;
    public string color;
    public string image_path;
}

[Serializable]
public class ClothingCatalogWrapper
{
    public ClothingCatalogItem[] Items;
}

public class RemyWardrobeViewer : MonoBehaviour
{
    private enum WardrobeSlot
    {
        Unknown,
        Top,
        Bottom,
        Shoes,
    }

    [Header("Backend Catalog")]
    public string backendUrl = "http://localhost:8000";
    public bool autoFetchCatalogOnStart = true;
    public int optionalUserIdFilter = -1;

    [Header("Avatar References")]
    public Transform avatarRoot;
    public Renderer topRenderer;
    public int topMaterialIndex;
    public Renderer bottomRenderer;
    public int bottomMaterialIndex;
    public Renderer shoesRenderer;
    public int shoesMaterialIndex;

    [Header("Overlay")]
    public bool showOverlay = true;
    public Vector2 overlayPosition = new Vector2(16f, 16f);
    public float overlayWidth = 430f;
    public float overlayHeight = 640f;

    [Header("Preview")]
    public bool preloadPreviewImages = true;

    private readonly List<ClothingCatalogItem> _items = new List<ClothingCatalogItem>();
    private readonly Dictionary<int, Texture2D> _previewTextures = new Dictionary<int, Texture2D>();
    private readonly HashSet<int> _requestedPreviewIds = new HashSet<int>();
    private readonly Dictionary<string, Texture2D> _defaultTextures = new Dictionary<string, Texture2D>();

    private Vector2 _scrollPosition;
    private GUIStyle _panelStyle;
    private GUIStyle _headerStyle;
    private GUIStyle _bodyStyle;
    private GUIStyle _buttonStyle;
    private bool _isFetchingCatalog;
    private string _statusMessage = "Chua tai catalog quan ao.";

    void Reset()
    {
        AutoAssignAvatarTargets();
    }

    void OnValidate()
    {
        if (avatarRoot != null && (topRenderer == null || bottomRenderer == null))
        {
            AutoAssignAvatarTargets();
        }
    }

    void Start()
    {
        AutoAssignAvatarTargets();
        CaptureDefaultTextures();

        if (autoFetchCatalogOnStart)
        {
            RefreshCatalog();
        }
    }

    [ContextMenu("Auto Assign Avatar Targets")]
    public void AutoAssignAvatarTargets()
    {
        if (avatarRoot == null)
        {
            return;
        }

        Renderer[] renderers = avatarRoot.GetComponentsInChildren<Renderer>(true);
        foreach (Renderer renderer in renderers)
        {
            Material[] materials = renderer.sharedMaterials;
            for (int i = 0; i < materials.Length; i++)
            {
                string materialName = materials[i] != null ? materials[i].name : string.Empty;
                string rendererName = renderer.name;

                if (topRenderer == null && MatchesAny(materialName, rendererName, "top", "shirt", "tshirt", "tee"))
                {
                    topRenderer = renderer;
                    topMaterialIndex = i;
                }

                if (bottomRenderer == null && MatchesAny(materialName, rendererName, "bottom", "pant", "trouser", "jean", "short"))
                {
                    bottomRenderer = renderer;
                    bottomMaterialIndex = i;
                }

                if (shoesRenderer == null && MatchesAny(materialName, rendererName, "shoe", "sneaker", "boot"))
                {
                    shoesRenderer = renderer;
                    shoesMaterialIndex = i;
                }
            }
        }

        if (topRenderer == null && renderers.Length > 0)
        {
            topRenderer = renderers[0];
            topMaterialIndex = 0;
        }

        if (bottomRenderer == null)
        {
            bottomRenderer = topRenderer;
            bottomMaterialIndex = Mathf.Min(1, GetMaterialCount(topRenderer) - 1);
            bottomMaterialIndex = Mathf.Max(0, bottomMaterialIndex);
        }

        Debug.Log(
            "[RemyWardrobeViewer] Auto-assign xong. " +
            "Top=" + DescribeRenderer(topRenderer, topMaterialIndex) + ", " +
            "Bottom=" + DescribeRenderer(bottomRenderer, bottomMaterialIndex) + ", " +
            "Shoes=" + DescribeRenderer(shoesRenderer, shoesMaterialIndex),
            this
        );
    }

    [ContextMenu("Print Avatar Material Slots")]
    public void PrintAvatarMaterialSlots()
    {
        if (avatarRoot == null)
        {
            Debug.LogWarning("[RemyWardrobeViewer] Chua gan avatarRoot.", this);
            return;
        }

        Renderer[] renderers = avatarRoot.GetComponentsInChildren<Renderer>(true);
        if (renderers == null || renderers.Length == 0)
        {
            Debug.LogWarning("[RemyWardrobeViewer] Khong tim thay Renderer nao trong avatarRoot.", this);
            return;
        }

        for (int i = 0; i < renderers.Length; i++)
        {
            Renderer renderer = renderers[i];
            Material[] materials = renderer.sharedMaterials;
            for (int materialIndex = 0; materialIndex < materials.Length; materialIndex++)
            {
                string materialName = materials[materialIndex] != null ? materials[materialIndex].name : "<null>";
                Debug.Log(
                    "[RemyWardrobeViewer] Renderer=" + renderer.name +
                    ", materialIndex=" + materialIndex +
                    ", material=" + materialName,
                    renderer
                );
            }
        }
    }

    [ContextMenu("Refresh Catalog")]
    public void RefreshCatalog()
    {
        if (!_isFetchingCatalog)
        {
            StartCoroutine(FetchCatalogCoroutine());
        }
    }

    [ContextMenu("Reset Outfit")]
    public void ResetOutfit()
    {
        RestoreDefaultTexture(topRenderer, topMaterialIndex);
        RestoreDefaultTexture(bottomRenderer, bottomMaterialIndex);
        RestoreDefaultTexture(shoesRenderer, shoesMaterialIndex);
        _statusMessage = "Da khoi phuc trang phuc mac dinh cua Remy.";
    }

    private IEnumerator FetchCatalogCoroutine()
    {
        _isFetchingCatalog = true;
        _statusMessage = "Dang tai danh sach quan ao...";

        string url = backendUrl + "/clothing-items?limit=500";
        if (optionalUserIdFilter > 0)
        {
            url += "&user_id=" + optionalUserIdFilter;
        }

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                _statusMessage = "Khong tai duoc catalog: " + request.error;
                _isFetchingCatalog = false;
                yield break;
            }

            string json = "{\"Items\":" + request.downloadHandler.text + "}";
            ClothingCatalogWrapper wrapper = JsonUtility.FromJson<ClothingCatalogWrapper>(json);

            _items.Clear();
            if (wrapper != null && wrapper.Items != null)
            {
                _items.AddRange(wrapper.Items);
            }

            _statusMessage = "Da tai " + _items.Count + " mon do.";

            if (preloadPreviewImages)
            {
                StartCoroutine(PreloadPreviewImagesCoroutine());
            }
        }

        _isFetchingCatalog = false;
    }

    private IEnumerator PreloadPreviewImagesCoroutine()
    {
        for (int i = 0; i < _items.Count; i++)
        {
            ClothingCatalogItem item = _items[i];
            if (item == null || string.IsNullOrWhiteSpace(item.image_path))
            {
                continue;
            }

            if (_previewTextures.ContainsKey(item.id) || _requestedPreviewIds.Contains(item.id))
            {
                continue;
            }

            yield return DownloadPreviewTextureCoroutine(item);
        }
    }

    private IEnumerator DownloadPreviewTextureCoroutine(ClothingCatalogItem item)
    {
        if (item == null || string.IsNullOrWhiteSpace(item.image_path))
        {
            yield break;
        }

        _requestedPreviewIds.Add(item.id);
        using (UnityWebRequest request = UnityWebRequestTexture.GetTexture(BuildAssetUrl(item.image_path)))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                Texture2D texture = DownloadHandlerTexture.GetContent(request);
                if (texture != null)
                {
                    _previewTextures[item.id] = texture;
                }
            }
        }
    }

    private void CaptureDefaultTextures()
    {
        CaptureDefaultTexture(topRenderer, topMaterialIndex);
        CaptureDefaultTexture(bottomRenderer, bottomMaterialIndex);
        CaptureDefaultTexture(shoesRenderer, shoesMaterialIndex);
    }

    private void CaptureDefaultTexture(Renderer renderer, int materialIndex)
    {
        Material material = GetMaterial(renderer, materialIndex);
        if (material == null)
        {
            return;
        }

        string key = BuildRendererKey(renderer, materialIndex);
        Texture2D texture = GetMainTexture(material);
        if (!_defaultTextures.ContainsKey(key))
        {
            _defaultTextures[key] = texture;
        }
    }

    private void RestoreDefaultTexture(Renderer renderer, int materialIndex)
    {
        string key = BuildRendererKey(renderer, materialIndex);
        if (!_defaultTextures.TryGetValue(key, out Texture2D texture))
        {
            return;
        }

        ApplyTexture(renderer, materialIndex, texture);
    }

    private void ApplyCatalogItem(ClothingCatalogItem item)
    {
        if (item == null)
        {
            return;
        }

        if (!_previewTextures.TryGetValue(item.id, out Texture2D texture) || texture == null)
        {
            StartCoroutine(DownloadAndApplyItemCoroutine(item));
            return;
        }

        ApplyItemTexture(item, texture);
    }

    private IEnumerator DownloadAndApplyItemCoroutine(ClothingCatalogItem item)
    {
        yield return DownloadPreviewTextureCoroutine(item);

        if (_previewTextures.TryGetValue(item.id, out Texture2D texture) && texture != null)
        {
            ApplyItemTexture(item, texture);
        }
        else
        {
            _statusMessage = "Khong tai duoc anh cho item #" + item.id;
        }
    }

    private void ApplyItemTexture(ClothingCatalogItem item, Texture2D texture)
    {
        WardrobeSlot slot = ResolveSlot(item.category);
        bool applied = false;

        if (slot == WardrobeSlot.Top || slot == WardrobeSlot.Unknown)
        {
            applied |= ApplyTexture(topRenderer, topMaterialIndex, texture);
        }

        if (slot == WardrobeSlot.Bottom)
        {
            applied |= ApplyTexture(bottomRenderer, bottomMaterialIndex, texture);
        }

        if (slot == WardrobeSlot.Shoes)
        {
            applied |= ApplyTexture(shoesRenderer, shoesMaterialIndex, texture);
        }

        if (!applied && slot == WardrobeSlot.Unknown)
        {
            applied |= ApplyTexture(bottomRenderer, bottomMaterialIndex, texture);
        }

        _statusMessage = applied
            ? "Dang mac item #" + item.id + " (" + SafeLabel(item.category) + ")."
            : "Chua ap duoc texture. Hay kiem tra renderer/material index.";

        Debug.Log(
            "[RemyWardrobeViewer] Apply item #" + item.id +
            " category=" + SafeLabel(item.category) +
            " slot=" + slot +
            " | Top=" + DescribeRenderer(topRenderer, topMaterialIndex) +
            " | Bottom=" + DescribeRenderer(bottomRenderer, bottomMaterialIndex) +
            " | Shoes=" + DescribeRenderer(shoesRenderer, shoesMaterialIndex),
            this
        );
    }

    private bool ApplyTexture(Renderer renderer, int materialIndex, Texture texture)
    {
        Material[] materials = GetMaterialArray(renderer);
        if (materials == null || materials.Length == 0)
        {
            return false;
        }

        int safeIndex = Mathf.Clamp(materialIndex, 0, materials.Length - 1);
        Material material = materials[safeIndex];
        if (material == null)
        {
            return false;
        }

        if (material.HasProperty("_BaseMap"))
        {
            material.SetTexture("_BaseMap", texture);
        }

        if (material.HasProperty("_MainTex"))
        {
            material.mainTexture = texture;
        }

        if (material.HasProperty("_BaseColor"))
        {
            material.SetColor("_BaseColor", Color.white);
        }

        if (material.HasProperty("_Color"))
        {
            material.SetColor("_Color", Color.white);
        }

        renderer.materials = materials;
        return true;
    }

    private Material[] GetMaterialArray(Renderer renderer)
    {
        if (renderer == null)
        {
            return null;
        }

        return renderer.materials;
    }

    private Material GetMaterial(Renderer renderer, int materialIndex)
    {
        Material[] materials = GetMaterialArray(renderer);
        if (materials == null || materials.Length == 0)
        {
            return null;
        }

        int safeIndex = Mathf.Clamp(materialIndex, 0, materials.Length - 1);
        return materials[safeIndex];
    }

    private int GetMaterialCount(Renderer renderer)
    {
        Material[] materials = GetMaterialArray(renderer);
        return materials != null ? materials.Length : 0;
    }

    private Texture2D GetMainTexture(Material material)
    {
        if (material == null)
        {
            return null;
        }

        if (material.HasProperty("_BaseMap"))
        {
            return material.GetTexture("_BaseMap") as Texture2D;
        }

        return material.mainTexture as Texture2D;
    }

    private string BuildAssetUrl(string imagePath)
    {
        if (string.IsNullOrWhiteSpace(imagePath))
        {
            return string.Empty;
        }

        if (imagePath.StartsWith("http://", StringComparison.OrdinalIgnoreCase) ||
            imagePath.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
        {
            return imagePath;
        }

        return backendUrl.TrimEnd('/') + "/" + imagePath.TrimStart('/');
    }

    private static string BuildRendererKey(Renderer renderer, int materialIndex)
    {
        if (renderer == null)
        {
            return "missing:" + materialIndex;
        }

        return renderer.GetInstanceID() + ":" + materialIndex;
    }

    private static bool MatchesAny(string materialName, string rendererName, params string[] keywords)
    {
        string combined = (materialName + " " + rendererName).ToLowerInvariant();
        for (int i = 0; i < keywords.Length; i++)
        {
            if (combined.Contains(keywords[i]))
            {
                return true;
            }
        }

        return false;
    }

    private static WardrobeSlot ResolveSlot(string category)
    {
        string normalized = string.IsNullOrWhiteSpace(category) ? string.Empty : category.ToLowerInvariant();

        if (normalized.Contains("shirt") || normalized.Contains("top") || normalized.Contains("tee") ||
            normalized.Contains("blouse") || normalized.Contains("hoodie") || normalized.Contains("jacket"))
        {
            return WardrobeSlot.Top;
        }

        if (normalized.Contains("pant") || normalized.Contains("trouser") || normalized.Contains("jean") ||
            normalized.Contains("short") || normalized.Contains("bottom") || normalized.Contains("skirt"))
        {
            return WardrobeSlot.Bottom;
        }

        if (normalized.Contains("shoe") || normalized.Contains("sneaker") || normalized.Contains("boot"))
        {
            return WardrobeSlot.Shoes;
        }

        return WardrobeSlot.Unknown;
    }

    private static string SafeLabel(string value)
    {
        return string.IsNullOrWhiteSpace(value) ? "unknown" : value;
    }

    private static string DescribeRenderer(Renderer renderer, int materialIndex)
    {
        if (renderer == null)
        {
            return "null";
        }

        Material[] materials = renderer.sharedMaterials;
        if (materials == null || materials.Length == 0)
        {
            return renderer.name + "[empty]";
        }

        int safeIndex = Mathf.Clamp(materialIndex, 0, materials.Length - 1);
        string materialName = materials[safeIndex] != null ? materials[safeIndex].name : "<null>";
        return renderer.name + "[" + safeIndex + ":" + materialName + "]";
    }

    private void EnsureStyles()
    {
        if (_panelStyle != null)
        {
            return;
        }

        _panelStyle = new GUIStyle(GUI.skin.box);
        _panelStyle.padding = new RectOffset(12, 12, 12, 12);

        _headerStyle = new GUIStyle(GUI.skin.label);
        _headerStyle.fontSize = 18;
        _headerStyle.fontStyle = FontStyle.Bold;
        _headerStyle.normal.textColor = Color.white;

        _bodyStyle = new GUIStyle(GUI.skin.label);
        _bodyStyle.wordWrap = true;
        _bodyStyle.normal.textColor = Color.white;

        _buttonStyle = new GUIStyle(GUI.skin.button);
        _buttonStyle.wordWrap = true;
    }

    void OnGUI()
    {
        if (!showOverlay)
        {
            return;
        }

        EnsureStyles();

        Color previousColor = GUI.color;
        GUI.color = new Color(0.08f, 0.1f, 0.14f, 0.92f);
        GUI.Box(new Rect(overlayPosition.x, overlayPosition.y, overlayWidth, overlayHeight), GUIContent.none, _panelStyle);
        GUI.color = previousColor;

        GUILayout.BeginArea(new Rect(overlayPosition.x + 10f, overlayPosition.y + 10f, overlayWidth - 20f, overlayHeight - 20f));
        GUILayout.Label("Remy Wardrobe Viewer", _headerStyle);
        GUILayout.Label(_statusMessage, _bodyStyle);

        GUILayout.BeginHorizontal();
        if (GUILayout.Button(_isFetchingCatalog ? "Dang tai..." : "Refresh Catalog", _buttonStyle, GUILayout.Height(32f)))
        {
            RefreshCatalog();
        }

        if (GUILayout.Button("Reset Outfit", _buttonStyle, GUILayout.Height(32f)))
        {
            ResetOutfit();
        }
        GUILayout.EndHorizontal();

        GUILayout.Space(8f);
        _scrollPosition = GUILayout.BeginScrollView(_scrollPosition);

        for (int i = 0; i < _items.Count; i++)
        {
            ClothingCatalogItem item = _items[i];
            DrawCatalogItem(item);
            GUILayout.Space(6f);
        }

        GUILayout.EndScrollView();
        GUILayout.EndArea();
    }

    private void DrawCatalogItem(ClothingCatalogItem item)
    {
        if (item == null)
        {
            return;
        }

        GUILayout.BeginVertical(GUI.skin.box);
        GUILayout.BeginHorizontal();

        Texture2D preview = null;
        _previewTextures.TryGetValue(item.id, out preview);

        if (preview != null)
        {
            GUILayout.Label(preview, GUILayout.Width(64f), GUILayout.Height(64f));
        }
        else
        {
            GUILayout.Box("No\nPreview", GUILayout.Width(64f), GUILayout.Height(64f));
        }

        GUILayout.BeginVertical();
        GUILayout.Label("#" + item.id + "  " + SafeLabel(item.category), _bodyStyle);
        GUILayout.Label("Mau: " + SafeLabel(item.color), _bodyStyle);
        GUILayout.Label("Size: " + SafeLabel(item.size_label), _bodyStyle);
        GUILayout.Label("Slot: " + ResolveSlot(item.category), _bodyStyle);

        if (GUILayout.Button("Mac mon nay", _buttonStyle, GUILayout.Height(28f)))
        {
            ApplyCatalogItem(item);
        }
        GUILayout.EndVertical();
        GUILayout.EndHorizontal();
        GUILayout.EndVertical();
    }
}
