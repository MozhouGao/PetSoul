using System;
using System.Collections;
using System.Threading.Tasks;
using GLTFast;
using UnityEngine;

namespace PetSoul
{
    public class ModelViewer : MonoBehaviour
    {
        public Transform Pivot;
        public OrbitCamera Orbit;
        public DogMotionPlayer Motion;
        public Light KeyLight;

        GltfImport _import;
        GameObject _instance;

        public bool IsLoaded => _instance != null;

        void Awake()
        {
            if (Pivot == null)
            {
                var go = new GameObject("ModelPivot");
                Pivot = go.transform;
            }
            if (KeyLight == null)
            {
                var lightGo = new GameObject("KeyLight");
                KeyLight = lightGo.AddComponent<Light>();
                KeyLight.type = LightType.Directional;
                KeyLight.intensity = 1.1f;
                lightGo.transform.rotation = Quaternion.Euler(40f, -30f, 0f);
            }
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.45f, 0.45f, 0.48f);
        }

        public IEnumerator Load(string path, Action<string> fail)
        {
            Clear();
            var uri = path.Contains("://") ? path : "file://" + path;
            _import = new GltfImport();
            var settings = new ImportSettings { AnimationMethod = AnimationMethod.Legacy };
            var loadTask = _import.Load(uri, settings);
            while (!loadTask.IsCompleted) yield return null;
            if (loadTask.IsFaulted || !loadTask.Result)
            {
                fail?.Invoke(loadTask.Exception != null ? loadTask.Exception.Message : "Could not load the GLB");
                yield break;
            }
            var instantiate = _import.InstantiateMainSceneAsync(Pivot);
            while (!instantiate.IsCompleted) yield return null;
            if (instantiate.IsFaulted || !instantiate.Result)
            {
                fail?.Invoke("Could not instantiate the GLB");
                yield break;
            }
            if (Pivot.childCount > 0) _instance = Pivot.GetChild(Pivot.childCount - 1).gameObject;
            Frame();
            if (Motion != null && _instance != null) Motion.Bind(_instance);
        }

        public void Frame()
        {
            var renderers = Pivot.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0 || Orbit == null) return;
            var bounds = renderers[0].bounds;
            for (var i = 1; i < renderers.Length; i++) bounds.Encapsulate(renderers[i].bounds);
            Orbit.Frame(bounds);
        }

        public byte[] CaptureThumbnail(Camera camera, int size = 256)
        {
            if (camera == null) return null;
            var rt = new RenderTexture(size, size, 16);
            var prev = camera.targetTexture;
            camera.targetTexture = rt;
            camera.Render();
            var prevActive = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(size, size, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, size, size), 0, 0);
            tex.Apply();
            camera.targetTexture = prev;
            RenderTexture.active = prevActive;
            var png = tex.EncodeToPNG();
            Destroy(tex);
            rt.Release();
            Destroy(rt);
            return png;
        }

        public void Clear()
        {
            if (_instance != null) Destroy(_instance);
            _instance = null;
            if (_import != null)
            {
                _import.Dispose();
                _import = null;
            }
            if (Pivot == null) return;
            for (var i = Pivot.childCount - 1; i >= 0; i--)
                Destroy(Pivot.GetChild(i).gameObject);
        }

        void OnDestroy() => Clear();
    }
}
