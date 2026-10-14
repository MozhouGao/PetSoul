using System.Collections;
using System.IO;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace PetSoul
{
    public class PetSoulBootstrap : MonoBehaviour
    {
        public string BackendUrl;

        void Awake()
        {
            if (FindObjectOfType<EventSystem>() == null)
            {
                var es = new GameObject("EventSystem");
                es.AddComponent<EventSystem>();
                es.AddComponent<StandaloneInputModule>();
            }

            var camGo = Camera.main != null ? Camera.main.gameObject : new GameObject("Main Camera");
            var cam = camGo.GetComponent<Camera>() ?? camGo.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.93f, 0.91f, 0.86f);
            camGo.tag = "MainCamera";
            camGo.AddComponent<AudioListener>();
            var orbit = camGo.GetComponent<OrbitCamera>() ?? camGo.AddComponent<OrbitCamera>();

            var canvasGo = new GameObject("Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = canvasGo.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1170, 2532);

            var api = gameObject.AddComponent<PetSoulAPI>();
            var photos = gameObject.AddComponent<PhotoCapture>();
            var storage = gameObject.AddComponent<ModelStorage>();
            var viewer = gameObject.AddComponent<ModelViewer>();
            var motion = gameObject.AddComponent<DogMotionPlayer>();
            var audio = gameObject.AddComponent<DogAudioPlayer>();
            viewer.Orbit = orbit;
            viewer.Motion = motion;
            audio.Bind(motion);

            var config = Resources.Load<TextAsset>("AppConfig");
            if (config != null)
            {
                var parsed = JsonConvert.DeserializeObject<AppConfig>(config.text);
                if (parsed != null && !string.IsNullOrEmpty(parsed.backendUrl))
                    api.BackendUrl = parsed.backendUrl;
                if (parsed != null && parsed.requestTimeoutSeconds > 0)
                    api.TimeoutSeconds = parsed.requestTimeoutSeconds;
            }
            if (!string.IsNullOrEmpty(BackendUrl)) api.BackendUrl = BackendUrl;
            var saved = PlayerPrefs.GetString("petsoul.backend", "");
            if (!string.IsNullOrEmpty(saved)) api.BackendUrl = saved;

            var ui = gameObject.AddComponent<UIManager>();
            ui.Init(canvas.transform, api, photos, storage, viewer, motion, audio, cam);
        }

        [System.Serializable]
        class AppConfig
        {
            public string backendUrl;
            public int requestTimeoutSeconds;
        }
    }
}
