using UnityEngine;

public class VRPerformanceMonitor : MonoBehaviour
{
    [Header("Display")]
    public bool showOverlay = true;
    public Vector2 overlayPosition = new Vector2(12f, 12f);
    [Range(10, 36)] public int fontSize = 18;
    [Range(1f, 3f)] public float uiScale = 1.5f;

    [Header("Sampling")]
    [Range(0.1f, 2f)] public float updateInterval = 0.5f;
    [Range(30f, 120f)] public float targetFps = 72f;

    [Header("Warning")]
    [Range(0.1f, 5f)] public float lowFpsSustainSeconds = 1.0f;
    public bool logLowFpsWarning = true;
    public bool logPeriodicSnapshot = true;
    [Range(1f, 30f)] public float snapshotIntervalSeconds = 5f;

    private float _timeLeft;
    private int _frameCount;
    private float _accumulatedDelta;
    private float _currentFps;
    private float _currentFrameMs;
    private float _lowFpsElapsed;
    private float _snapshotElapsed;
    private GUIStyle _boxStyle;
    private GUIStyle _labelStyle;

    void OnEnable()
    {
        _timeLeft = updateInterval;
        _snapshotElapsed = 0f;
    }

    void Update()
    {
        float delta = Time.unscaledDeltaTime;
        _timeLeft -= delta;
        _frameCount += 1;
        _accumulatedDelta += delta;

        if (delta > 0f)
        {
            float instantFps = 1f / delta;
            if (instantFps < targetFps)
            {
                _lowFpsElapsed += delta;
                if (logLowFpsWarning && _lowFpsElapsed >= lowFpsSustainSeconds)
                {
                    Debug.LogWarning($"[VRPerformanceMonitor] FPS thấp kéo dài: {instantFps:F1} (< {targetFps:F0})");
                    _lowFpsElapsed = 0f;
                }
            }
            else
            {
                _lowFpsElapsed = 0f;
            }
        }

        if (_timeLeft > 0f)
        {
            return;
        }

        if (_accumulatedDelta > 0f)
        {
            _currentFps = _frameCount / _accumulatedDelta;
            _currentFrameMs = 1000f / Mathf.Max(_currentFps, 0.0001f);
        }

        _timeLeft = updateInterval;
        _frameCount = 0;
        _accumulatedDelta = 0f;

        if (logPeriodicSnapshot)
        {
            _snapshotElapsed += updateInterval;
            if (_snapshotElapsed >= snapshotIntervalSeconds)
            {
                Debug.Log($"[VRPerformanceMonitor] FPS={_currentFps:F1}, Frame={_currentFrameMs:F2} ms, Target={targetFps:F0}");
                _snapshotElapsed = 0f;
            }
        }
    }

    void EnsureGuiStyles()
    {
        if (_boxStyle != null && _labelStyle != null)
        {
            return;
        }

        _boxStyle = new GUIStyle(GUI.skin.box);
        _boxStyle.alignment = TextAnchor.UpperLeft;
        _boxStyle.padding = new RectOffset(10, 10, 8, 8);

        _labelStyle = new GUIStyle(GUI.skin.label);
        _labelStyle.fontSize = fontSize;
        _labelStyle.fontStyle = FontStyle.Bold;
        _labelStyle.normal.textColor = Color.white;
    }

    void OnGUI()
    {
        if (!showOverlay)
        {
            return;
        }

        EnsureGuiStyles();

        Matrix4x4 previousMatrix = GUI.matrix;
        GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(uiScale, uiScale, 1f));

        string status = _currentFps >= targetFps ? "OK" : "LOW";

        Color boxColor = _currentFps >= targetFps ? new Color(0f, 0.25f, 0f, 0.65f) : new Color(0.35f, 0.25f, 0f, 0.7f);
        Color previousColor = GUI.color;
        GUI.color = boxColor;
        GUI.Box(new Rect(overlayPosition.x, overlayPosition.y, 340f, 120f), GUIContent.none, _boxStyle);

        GUI.color = Color.white;
        GUI.Label(new Rect(overlayPosition.x + 8f, overlayPosition.y + 6f, 330f, 110f),
            $"FPS: {_currentFps:F1}\nFrame: {_currentFrameMs:F2} ms\nTarget: {targetFps:F0} ({status})", _labelStyle);

        GUI.color = previousColor;
        GUI.matrix = previousMatrix;
        GUI.color = Color.white;
    }
}
