using UnityEngine;

public class VRClothOptimizer : MonoBehaviour
{
    [Header("Target Target Components")]
    public Cloth[] clothComponents;

    [Header("Performance Thresholds")]
    public float checkIntervalSeconds = 2.0f;
    public float criticalFpsThreshold = 60f;

    // Lưu trữ cấu hình gốc
    private bool[] _originalEnabledState;

    private float _deltaTime = 0f;
    private float _timer = 0f;

    void Start()
    {
        if (clothComponents == null || clothComponents.Length == 0)
        {
            clothComponents = GetComponentsInChildren<Cloth>(true); // lấy cả obj đang disable
        }

        _originalEnabledState = new bool[clothComponents.Length];
        for (int i = 0; i < clothComponents.Length; i++)
        {
            if (clothComponents[i] != null)
            {
                _originalEnabledState[i] = clothComponents[i].enabled;
            }
        }
    }

    void Update()
    {
        // Tính toán deltaTime trung bình để đo FPS
        _deltaTime += (Time.unscaledDeltaTime - _deltaTime) * 0.1f;
        _timer += Time.unscaledDeltaTime;

        // Định kỳ kiểm tra FPS
        if (_timer >= checkIntervalSeconds)
        {
            _timer = 0f;
            float fps = 1.0f / _deltaTime;
            AdjustClothPerformance(fps);
        }
    }

    private void AdjustClothPerformance(float currentFps)
    {
        bool shouldDisable = currentFps < criticalFpsThreshold;

        for (int i = 0; i < clothComponents.Length; i++)
        {
            Cloth c = clothComponents[i];
            if (c == null) continue;

            if (shouldDisable)
            {
                // Nguy hiểm -> Tắt hẳn Cloth
                c.enabled = false;
            }
            else
            {
                // Bình thường -> Phục hồi
                c.enabled = _originalEnabledState[i];
            }
        }
    }
}
