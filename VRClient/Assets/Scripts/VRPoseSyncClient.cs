using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class PoseEstimateResponseData
{
    public int image_width;
    public int image_height;
    public PoseKeypointData[] keypoints;
}

[Serializable]
public class PoseKeypointData
{
    public int index;
    public string name;
    public float x;
    public float y;
    public float z;
    public int pixel_x;
    public int pixel_y;
    public float visibility;
}

public class VRPoseSyncClient : MonoBehaviour
{
    [Header("Backend Pose")]
    public string backendUrl = "http://localhost:8000";
    [Min(80f)] public float referenceHeightCm = 170f;
    public Texture2D sourcePoseImage;

    [Header("Avatar Rig")]
    public Animator targetAnimator;
    [Range(1f, 30f)] public float rotationLerpSpeed = 12f;
    [Range(0.1f, 3f)] public float poseWidthScale = 1.0f;
    [Range(0.1f, 3f)] public float poseHeightScale = 1.45f;
    [Range(0.05f, 2f)] public float depthScale = 0.2f;

    [Header("Pose Stability")]
    public bool freezeAnimatorWhenApplyingPose = true;
    public bool applyInstantlyForStaticEstimate = true;
    public bool usePoseDepth = false;
    public bool usePoseDepthForLegs = true;
    [Range(0.05f, 1.5f)] public float maxDepthOffset = 0.45f;
    [Range(0f, 0.1f)] public float minLeftRightGap = 0.02f;

    [Header("Human-like Limits")]
    public bool useHumanLikeJointLimits = true;
    [Range(10f, 120f)] public float maxUpperLegAngleFromBind = 60f;
    [Range(20f, 140f)] public float maxLowerLegAngleFromBind = 75f;
    [Range(20f, 140f)] public float maxUpperArmAngleFromBind = 95f;
    [Range(20f, 170f)] public float maxLowerArmAngleFromBind = 120f;
    [Range(10f, 80f)] public float maxSpineAngleFromBind = 35f;

    [Header("Seated Pose Assist")]
    [Range(0f, 1.5f)] public float seatedBendAssist = 1.15f;
    [Range(0f, 120f)] public float seatedBendThreshold = 12f;
    [Range(-1f, 1f)] public float bendAxisDirection = -1f;

    private readonly Dictionary<string, PoseKeypointData> _keypoints = new Dictionary<string, PoseKeypointData>();
    private readonly Dictionary<HumanBodyBones, Transform> _boneMap = new Dictionary<HumanBodyBones, Transform>();
    private readonly Dictionary<HumanBodyBones, Vector3> _bindBoneDirections = new Dictionary<HumanBodyBones, Vector3>();
    private readonly Dictionary<HumanBodyBones, Quaternion> _bindLocalRotations = new Dictionary<HumanBodyBones, Quaternion>();
    private readonly Dictionary<HumanBodyBones, float> _boneMaxAngleLimits = new Dictionary<HumanBodyBones, float>();

    [ContextMenu("Estimate Pose And Apply To Rig")]
    public void EstimatePoseAndApplyToRig()
    {
        if (sourcePoseImage == null)
        {
            Debug.LogWarning("Thiếu sourcePoseImage để gửi sang endpoint /pose/estimate.");
            return;
        }

        if (freezeAnimatorWhenApplyingPose && targetAnimator != null && targetAnimator.enabled)
        {
            targetAnimator.enabled = false;
        }

        StartCoroutine(PostEstimateAndApply());
    }

    [ContextMenu("Apply Recommended Demo Settings")]
    public void ApplyRecommendedDemoSettings()
    {
        freezeAnimatorWhenApplyingPose = true;
        applyInstantlyForStaticEstimate = true;
        usePoseDepth = false;
        usePoseDepthForLegs = true;
        poseWidthScale = 1.0f;
        poseHeightScale = 1.45f;
        depthScale = 0.2f;
        maxDepthOffset = 0.4f;
        minLeftRightGap = 0.02f;
        seatedBendAssist = 1.15f;
        seatedBendThreshold = 12f;
        bendAxisDirection = -1f;
        rotationLerpSpeed = 12f;
        useHumanLikeJointLimits = true;
        maxUpperLegAngleFromBind = 60f;
        maxLowerLegAngleFromBind = 75f;
        maxUpperArmAngleFromBind = 95f;
        maxLowerArmAngleFromBind = 120f;
        maxSpineAngleFromBind = 35f;
        Debug.Log("Applied recommended demo settings for static image pose tests.", this);
    }

    private IEnumerator PostEstimateAndApply()
    {
        EnsureRigCache();
        if (_boneMap.Count == 0)
        {
            yield break;
        }

        byte[] pngBytes = EncodeTextureToPngSafe(sourcePoseImage);
        if (pngBytes == null || pngBytes.Length == 0)
        {
            Debug.LogError("Không encode được sourcePoseImage thành PNG.");
            yield break;
        }

        WWWForm form = new WWWForm();
        form.AddField("reference_height_cm", referenceHeightCm.ToString(System.Globalization.CultureInfo.InvariantCulture));
        form.AddBinaryData("file", pngBytes, "pose_input.png", "image/png");

        using (UnityWebRequest request = UnityWebRequest.Post(backendUrl + "/pose/estimate", form))
        {
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                string serverDetail = request.downloadHandler != null ? request.downloadHandler.text : string.Empty;
                if (!string.IsNullOrWhiteSpace(serverDetail))
                {
                    Debug.LogError("Lỗi gọi /pose/estimate: " + request.error + " | detail=" + serverDetail);
                }
                else
                {
                    Debug.LogError("Lỗi gọi /pose/estimate: " + request.error);
                }
                yield break;
            }

            PoseEstimateResponseData payload = JsonUtility.FromJson<PoseEstimateResponseData>(request.downloadHandler.text);
            if (payload == null || payload.keypoints == null || payload.keypoints.Length == 0)
            {
                Debug.LogError("Không parse được response keypoints từ backend.");
                yield break;
            }

            CacheKeypoints(payload.keypoints);
            ApplyPoseToRig();
            Debug.Log("Da map keypoints vao rig thanh cong (baseline).", this);
        }
    }

    private static byte[] EncodeTextureToPngSafe(Texture2D texture)
    {
        if (texture == null)
        {
            return null;
        }

        try
        {
            return texture.EncodeToPNG();
        }
        catch (ArgumentException)
        {
            // Some imported textures are not readable; copy pixels through a RenderTexture.
            RenderTexture rt = RenderTexture.GetTemporary(texture.width, texture.height, 0, RenderTextureFormat.ARGB32);
            RenderTexture previous = RenderTexture.active;
            Texture2D readableCopy = null;
            try
            {
                Graphics.Blit(texture, rt);
                RenderTexture.active = rt;

                readableCopy = new Texture2D(texture.width, texture.height, TextureFormat.RGBA32, false);
                readableCopy.ReadPixels(new Rect(0, 0, texture.width, texture.height), 0, 0);
                readableCopy.Apply(false, false);
                return readableCopy.EncodeToPNG();
            }
            finally
            {
                RenderTexture.active = previous;
                RenderTexture.ReleaseTemporary(rt);
                if (readableCopy != null)
                {
                    Destroy(readableCopy);
                }
            }
        }
    }

    private void EnsureRigCache()
    {
        if (_boneMap.Count > 0)
        {
            return;
        }

        if (targetAnimator == null)
        {
            targetAnimator = GetComponentInChildren<Animator>();
        }

        if (targetAnimator == null)
        {
            Debug.LogWarning("Không tìm thấy Animator để map bone.");
            return;
        }

        RegisterBone(HumanBodyBones.Spine, HumanBodyBones.Chest);
        RegisterBone(HumanBodyBones.Chest, HumanBodyBones.Neck);

        RegisterBone(HumanBodyBones.LeftUpperArm, HumanBodyBones.LeftLowerArm);
        RegisterBone(HumanBodyBones.LeftLowerArm, HumanBodyBones.LeftHand);
        RegisterBone(HumanBodyBones.RightUpperArm, HumanBodyBones.RightLowerArm);
        RegisterBone(HumanBodyBones.RightLowerArm, HumanBodyBones.RightHand);

        RegisterBone(HumanBodyBones.LeftUpperLeg, HumanBodyBones.LeftLowerLeg);
        RegisterBone(HumanBodyBones.LeftLowerLeg, HumanBodyBones.LeftFoot);
        RegisterBone(HumanBodyBones.RightUpperLeg, HumanBodyBones.RightLowerLeg);
        RegisterBone(HumanBodyBones.RightLowerLeg, HumanBodyBones.RightFoot);

        InitializeBoneLimits();
    }

    private void InitializeBoneLimits()
    {
        _boneMaxAngleLimits[HumanBodyBones.LeftUpperLeg] = maxUpperLegAngleFromBind;
        _boneMaxAngleLimits[HumanBodyBones.RightUpperLeg] = maxUpperLegAngleFromBind;
        _boneMaxAngleLimits[HumanBodyBones.LeftLowerLeg] = maxLowerLegAngleFromBind;
        _boneMaxAngleLimits[HumanBodyBones.RightLowerLeg] = maxLowerLegAngleFromBind;
        _boneMaxAngleLimits[HumanBodyBones.LeftUpperArm] = maxUpperArmAngleFromBind;
        _boneMaxAngleLimits[HumanBodyBones.RightUpperArm] = maxUpperArmAngleFromBind;
        _boneMaxAngleLimits[HumanBodyBones.LeftLowerArm] = maxLowerArmAngleFromBind;
        _boneMaxAngleLimits[HumanBodyBones.RightLowerArm] = maxLowerArmAngleFromBind;
        _boneMaxAngleLimits[HumanBodyBones.Spine] = maxSpineAngleFromBind;
        _boneMaxAngleLimits[HumanBodyBones.Chest] = maxSpineAngleFromBind;
    }

    private void RegisterBone(HumanBodyBones bone, HumanBodyBones childBone)
    {
        Transform boneTf = targetAnimator.GetBoneTransform(bone);
        Transform childTf = targetAnimator.GetBoneTransform(childBone);
        if (boneTf == null || childTf == null)
        {
            return;
        }

        _boneMap[bone] = boneTf;
        _bindLocalRotations[bone] = boneTf.localRotation;
        Vector3 worldDir = (childTf.position - boneTf.position).normalized;
        _bindBoneDirections[bone] = boneTf.InverseTransformDirection(worldDir);
    }

    private void ResetMappedBonesToBindPose()
    {
        foreach (KeyValuePair<HumanBodyBones, Transform> pair in _boneMap)
        {
            if (_bindLocalRotations.TryGetValue(pair.Key, out Quaternion bindLocalRotation))
            {
                pair.Value.localRotation = bindLocalRotation;
            }
        }
    }

    private void CacheKeypoints(PoseKeypointData[] points)
    {
        _keypoints.Clear();
        for (int i = 0; i < points.Length; i++)
        {
            PoseKeypointData p = points[i];
            if (!string.IsNullOrEmpty(p.name))
            {
                _keypoints[p.name] = p;
            }
        }

        StabilizeLowerBodyLateralOrder();
    }

    private void StabilizeLowerBodyLateralOrder()
    {
        EnsureLateralOrder("left_hip", "right_hip");
        EnsureLateralOrder("left_knee", "right_knee");
        EnsureLateralOrder("left_ankle", "right_ankle");
        EnsureLateralOrder("left_foot_index", "right_foot_index");
    }

    private void EnsureLateralOrder(string leftName, string rightName)
    {
        if (!_keypoints.TryGetValue(leftName, out PoseKeypointData left) ||
            !_keypoints.TryGetValue(rightName, out PoseKeypointData right))
        {
            return;
        }

        // MediaPipe usually yields left-side landmarks with larger x when the subject faces camera.
        float desiredGap = Mathf.Max(minLeftRightGap, 0.001f);
        if (left.x <= right.x + desiredGap)
        {
            float center = (left.x + right.x) * 0.5f;
            left.x = Mathf.Clamp01(center + desiredGap * 0.5f);
            right.x = Mathf.Clamp01(center - desiredGap * 0.5f);
        }

        _keypoints[leftName] = left;
        _keypoints[rightName] = right;
    }

    private static bool IsLegKeypoint(string keypointName)
    {
        return keypointName.Contains("hip") ||
               keypointName.Contains("knee") ||
               keypointName.Contains("ankle") ||
               keypointName.Contains("heel") ||
               keypointName.Contains("foot");
    }

    private Vector3 ToAvatarSpace(string keypointName, PoseKeypointData p)
    {
        float x = (p.x - 0.5f) * poseWidthScale;
        float y = (0.5f - p.y) * poseHeightScale;
        float z = 0f;
        bool depthEnabled = usePoseDepth || (usePoseDepthForLegs && IsLegKeypoint(keypointName));
        if (depthEnabled)
        {
            float clampedDepth = Mathf.Clamp(-p.z, -maxDepthOffset, maxDepthOffset);
            z = clampedDepth * depthScale;
        }
        return targetAnimator.transform.TransformPoint(new Vector3(x, y, z));
    }

    private bool TryDirection(string fromName, string toName, out Vector3 direction)
    {
        direction = Vector3.forward;
        if (!_keypoints.TryGetValue(fromName, out PoseKeypointData from) || !_keypoints.TryGetValue(toName, out PoseKeypointData to))
        {
            return false;
        }

        Vector3 fromPos = ToAvatarSpace(fromName, from);
        Vector3 toPos = ToAvatarSpace(toName, to);
        Vector3 dir = toPos - fromPos;
        if (dir.sqrMagnitude < 0.000001f)
        {
            return false;
        }

        direction = dir.normalized;
        return true;
    }

    private void ApplyPoseToRig()
    {
        // Prevent cumulative drift between multiple estimates on static-image workflow.
        ResetMappedBonesToBindPose();

        TryRotateBone(HumanBodyBones.LeftUpperArm, "left_shoulder", "left_elbow");
        TryRotateBone(HumanBodyBones.LeftLowerArm, "left_elbow", "left_wrist");
        TryRotateBone(HumanBodyBones.RightUpperArm, "right_shoulder", "right_elbow");
        TryRotateBone(HumanBodyBones.RightLowerArm, "right_elbow", "right_wrist");

        TryRotateBone(HumanBodyBones.LeftUpperLeg, "left_hip", "left_knee");
        TryRotateBone(HumanBodyBones.LeftLowerLeg, "left_knee", "left_ankle");
        TryRotateBone(HumanBodyBones.RightUpperLeg, "right_hip", "right_knee");
        TryRotateBone(HumanBodyBones.RightLowerLeg, "right_knee", "right_ankle");

        // Spine uses centerline between hips and shoulders for stable torso orientation.
        if (TryCenterDirection("left_hip", "right_hip", "left_shoulder", "right_shoulder", out Vector3 torsoDir))
        {
            RotateBoneTowards(HumanBodyBones.Spine, torsoDir);
            RotateBoneTowards(HumanBodyBones.Chest, torsoDir);
        }

        ApplySeatedBendAssist();
    }

    private void ApplySeatedBendAssist()
    {
        if (seatedBendAssist <= 0f)
        {
            return;
        }

        ApplySeatedBendToLeg(
            "left_hip",
            "left_knee",
            "left_ankle",
            HumanBodyBones.LeftUpperLeg,
            HumanBodyBones.LeftLowerLeg
        );

        ApplySeatedBendToLeg(
            "right_hip",
            "right_knee",
            "right_ankle",
            HumanBodyBones.RightUpperLeg,
            HumanBodyBones.RightLowerLeg
        );
    }

    private void ApplySeatedBendToLeg(
        string hipName,
        string kneeName,
        string ankleName,
        HumanBodyBones upperLegBone,
        HumanBodyBones lowerLegBone
    )
    {
        if (!TryGetJointBendDegrees(hipName, kneeName, ankleName, out float bendDegrees))
        {
            return;
        }

        float effectiveBend = Mathf.Max(0f, bendDegrees - seatedBendThreshold) * seatedBendAssist;
        if (effectiveBend <= 0f)
        {
            return;
        }

        if (_boneMap.TryGetValue(upperLegBone, out Transform upperLegTf))
        {
            upperLegTf.localRotation = Quaternion.AngleAxis(effectiveBend * 0.42f * bendAxisDirection, Vector3.right) * upperLegTf.localRotation;
        }

        if (_boneMap.TryGetValue(lowerLegBone, out Transform lowerLegTf))
        {
            lowerLegTf.localRotation = Quaternion.AngleAxis(effectiveBend * -0.68f * bendAxisDirection, Vector3.right) * lowerLegTf.localRotation;
        }
    }

    private bool TryGetJointBendDegrees(string aName, string jointName, string bName, out float bendDegrees)
    {
        bendDegrees = 0f;

        if (!_keypoints.TryGetValue(aName, out PoseKeypointData a) ||
            !_keypoints.TryGetValue(jointName, out PoseKeypointData joint) ||
            !_keypoints.TryGetValue(bName, out PoseKeypointData b))
        {
            return false;
        }

        Vector2 v1 = new Vector2(a.x - joint.x, a.y - joint.y);
        Vector2 v2 = new Vector2(b.x - joint.x, b.y - joint.y);
        if (v1.sqrMagnitude < 1e-6f || v2.sqrMagnitude < 1e-6f)
        {
            return false;
        }

        float angle = Vector2.Angle(v1, v2);
        bendDegrees = Mathf.Clamp(180f - angle, 0f, 140f);
        return true;
    }

    private bool TryCenterDirection(string fromA, string fromB, string toA, string toB, out Vector3 direction)
    {
        direction = Vector3.forward;
        if (!_keypoints.TryGetValue(fromA, out PoseKeypointData p1) ||
            !_keypoints.TryGetValue(fromB, out PoseKeypointData p2) ||
            !_keypoints.TryGetValue(toA, out PoseKeypointData p3) ||
            !_keypoints.TryGetValue(toB, out PoseKeypointData p4))
        {
            return false;
        }

        Vector3 fromCenter = (ToAvatarSpace(fromA, p1) + ToAvatarSpace(fromB, p2)) * 0.5f;
        Vector3 toCenter = (ToAvatarSpace(toA, p3) + ToAvatarSpace(toB, p4)) * 0.5f;
        Vector3 dir = toCenter - fromCenter;
        if (dir.sqrMagnitude < 0.000001f)
        {
            return false;
        }

        direction = dir.normalized;
        return true;
    }

    private void TryRotateBone(HumanBodyBones bone, string fromName, string toName)
    {
        if (TryDirection(fromName, toName, out Vector3 dir))
        {
            RotateBoneTowards(bone, dir);
        }
    }

    private void RotateBoneTowards(HumanBodyBones bone, Vector3 targetDir)
    {
        if (!_boneMap.TryGetValue(bone, out Transform boneTf))
        {
            return;
        }

        if (!_bindBoneDirections.TryGetValue(bone, out Vector3 localBindDir))
        {
            return;
        }

        Vector3 currentForward = boneTf.TransformDirection(localBindDir).normalized;
        Quaternion delta = Quaternion.FromToRotation(currentForward, targetDir);
        Quaternion targetRotation = delta * boneTf.rotation;

        if (useHumanLikeJointLimits)
        {
            targetRotation = ClampRotationToBindLimit(bone, boneTf, targetRotation);
        }

        float t = applyInstantlyForStaticEstimate ? 1f : 1f - Mathf.Exp(-rotationLerpSpeed * Time.deltaTime);
        boneTf.rotation = Quaternion.Slerp(boneTf.rotation, targetRotation, t);
    }

    private Quaternion ClampRotationToBindLimit(HumanBodyBones bone, Transform boneTf, Quaternion targetWorldRotation)
    {
        if (!_bindLocalRotations.TryGetValue(bone, out Quaternion bindLocalRotation))
        {
            return targetWorldRotation;
        }

        if (!_boneMaxAngleLimits.TryGetValue(bone, out float maxAngle))
        {
            return targetWorldRotation;
        }

        Quaternion parentWorldRotation = boneTf.parent != null ? boneTf.parent.rotation : Quaternion.identity;
        Quaternion targetLocalRotation = Quaternion.Inverse(parentWorldRotation) * targetWorldRotation;
        float localDeltaAngle = Quaternion.Angle(bindLocalRotation, targetLocalRotation);
        if (localDeltaAngle <= maxAngle)
        {
            return targetWorldRotation;
        }

        float ratio = Mathf.Clamp01(maxAngle / Mathf.Max(localDeltaAngle, 0.0001f));
        Quaternion clampedLocalRotation = Quaternion.Slerp(bindLocalRotation, targetLocalRotation, ratio);
        return parentWorldRotation * clampedLocalRotation;
    }
}
