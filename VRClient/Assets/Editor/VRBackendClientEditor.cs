using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(VRBackendClient))]
public class VRBackendClientEditor : Editor
{
    public override void OnInspectorGUI()
    {
        DrawDefaultInspector();

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Quick Actions", EditorStyles.boldLabel);

        var client = (VRBackendClient)target;

        if (GUILayout.Button("Auto Assign Avatar Renderer"))
        {
            Undo.RecordObject(client, "Auto Assign Avatar Renderer");
            client.TryAutoAssignAvatarRenderer();
            EditorUtility.SetDirty(client);
        }

        GUI.enabled = Application.isPlaying;

        if (GUILayout.Button("Test Backend Connection"))
        {
            client.StartHealthCheck();
        }

        if (GUILayout.Button("Run Test Request Fitting"))
        {
            client.RunFittingWorkflow();
        }

        GUI.enabled = true;

        if (!Application.isPlaying)
        {
            EditorGUILayout.HelpBox("Enter Play mode to run the fitting test buttons.", MessageType.Info);
        }
    }
}
