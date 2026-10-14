using UnityEditor;
using UnityEditor.Build;
using UnityEngine;

namespace PetSoul.EditorTools
{
    public static class IosProjectSetup
    {
        [MenuItem("Pet Soul/Configure iOS Player")]
        public static void Configure()
        {
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.iOS, "com.muffinman.petsoul");
            PlayerSettings.iOS.targetOSVersionString = "15.0";
            PlayerSettings.iOS.cameraUsageDescription = "Take a photo of your pet to build a 3D model.";
            PlayerSettings.iOS.photoLibraryUsageDescription = "Choose a pet photo or video from your library.";
            PlayerSettings.iOS.microphoneUsageDescription = "Record your pet so the model can use that voice.";
            PlayerSettings.insecureHttpOption = InsecureHttpOption.AlwaysAllowed;
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene("Assets/Scenes/MainScene.unity", true),
            };
            Debug.Log("Pet Soul iOS player settings applied. Use your Mac LAN IP in the app, then HTTPS for TestFlight.");
        }
    }
}
