using UnityEngine;

public class AvatarColliderBuilder : MonoBehaviour
{
    [Header("Settings")]
    public float boneThicknessRadius = 0.04f;
    public PhysicsMaterial optimizedPhysicMaterial;

    [ContextMenu("Auto Generate Colliders for VR")]
    public void GenerateColliders()
    {
        Animator animator = GetComponent<Animator>();
        if (animator == null)
        {
            Debug.LogError("Cần có Animator (Humanoid) để tự động gắn collider.");
            return;
        }

        // Xóa các collider cũ nếu cần làm lại
        RemoveExistingColliders(animator.transform);

        // Map các xương cần gắn Capsule Collider
        AddCapsule(animator, HumanBodyBones.LeftUpperLeg, HumanBodyBones.LeftLowerLeg);
        AddCapsule(animator, HumanBodyBones.LeftLowerLeg, HumanBodyBones.LeftFoot);
        AddCapsule(animator, HumanBodyBones.RightUpperLeg, HumanBodyBones.RightLowerLeg);
        AddCapsule(animator, HumanBodyBones.RightLowerLeg, HumanBodyBones.RightFoot);
        
        AddCapsule(animator, HumanBodyBones.LeftUpperArm, HumanBodyBones.LeftLowerArm);
        AddCapsule(animator, HumanBodyBones.LeftLowerArm, HumanBodyBones.LeftHand);
        AddCapsule(animator, HumanBodyBones.RightUpperArm, HumanBodyBones.RightLowerArm);
        AddCapsule(animator, HumanBodyBones.RightLowerArm, HumanBodyBones.RightHand);

        AddCapsule(animator, HumanBodyBones.Spine, HumanBodyBones.Chest);
        
        // Sphere cho đầu
        Transform head = animator.GetBoneTransform(HumanBodyBones.Head);
        if (head != null)
        {
            SphereCollider sc = head.gameObject.AddComponent<SphereCollider>();
            sc.radius = 0.12f;
            sc.center = new Vector3(0, 0.05f, 0); // Ước tính tương đối
            if (optimizedPhysicMaterial != null) sc.material = optimizedPhysicMaterial;
        }

        Debug.Log("<color=green>✅ Đã tự động tạo các Collider tối ưu hiệu năng VR cho Avatar.</color>");
    }

    [ContextMenu("Remove Existing Colliders")]
    public void RemoveExistingCollidersList()
    {
        RemoveExistingColliders(transform);
        Debug.Log("Đã dọn dẹp Capsule/Sphere Collider cũ.");
    }

    private void RemoveExistingColliders(Transform root)
    {
        Collider[] colliders = root.GetComponentsInChildren<Collider>();
        foreach (var col in colliders)
        {
            if (col is CapsuleCollider || col is SphereCollider)
            {
                DestroyImmediate(col);
            }
        }
    }

    private void AddCapsule(Animator animator, HumanBodyBones startBone, HumanBodyBones endBone)
    {
        Transform start = animator.GetBoneTransform(startBone);
        Transform end = animator.GetBoneTransform(endBone);

        if (start == null || end == null) return;

        CapsuleCollider cap = start.gameObject.AddComponent<CapsuleCollider>();
        if (optimizedPhysicMaterial != null) cap.material = optimizedPhysicMaterial;

        Vector3 boneDirection = end.position - start.position;
        float length = boneDirection.magnitude;

        cap.radius = boneThicknessRadius;
        cap.height = length;
        
        // Unity CapsuleCollider direction: 0 = X, 1 = Y, 2 = Z
        // Tìm trục hướng về end bone gần nhất
        Vector3 localDir = start.InverseTransformDirection(boneDirection.normalized);
        if (Mathf.Abs(localDir.x) > Mathf.Abs(localDir.y) && Mathf.Abs(localDir.x) > Mathf.Abs(localDir.z))
            cap.direction = 0;
        else if (Mathf.Abs(localDir.y) > Mathf.Abs(localDir.x) && Mathf.Abs(localDir.y) > Mathf.Abs(localDir.z))
            cap.direction = 1;
        else
            cap.direction = 2;

        // Căn giữa capsule
        cap.center = start.InverseTransformVector(boneDirection * 0.5f);
    }
}
