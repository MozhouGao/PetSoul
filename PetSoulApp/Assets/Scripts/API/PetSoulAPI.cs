using System;
using System.Collections;
using System.Text;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.Networking;

namespace PetSoul
{
    public class PetSoulAPI : MonoBehaviour
    {
        public string BackendUrl = "http://127.0.0.1:8000";
        public int TimeoutSeconds = 300;

        public IEnumerator CheckHealth(Action<bool> done)
        {
            using var req = UnityWebRequest.Get(Url("/health"));
            req.timeout = 8;
            yield return req.SendWebRequest();
            done(req.result == UnityWebRequest.Result.Success);
        }

        public IEnumerator Generate(byte[] jpeg, Action<string> status, Action<GenerateResponse> ok, Action<string> fail)
        {
            status?.Invoke("Uploading photo...");
            var form = new WWWForm();
            form.AddBinaryData("file", jpeg, "pet.jpg", "image/jpeg");
            using var req = UnityWebRequest.Post(Url("/generate-3d-model"), form);
            req.timeout = TimeoutSeconds;
            var op = req.SendWebRequest();
            while (!op.isDone)
            {
                status?.Invoke(req.uploadProgress < 0.99f
                    ? "Uploading photo..."
                    : "Detecting pet...\nGenerating 3D model... (1–3 minutes)");
                yield return null;
            }

            if (req.result != UnityWebRequest.Result.Success)
            {
                fail?.Invoke(string.IsNullOrEmpty(req.error) ? "Request timed out" : req.error);
                yield break;
            }

            GenerateResponse parsed;
            try
            {
                parsed = JsonConvert.DeserializeObject<GenerateResponse>(req.downloadHandler.text);
            }
            catch (Exception ex)
            {
                fail?.Invoke(ex.Message);
                yield break;
            }

            if (parsed == null || string.IsNullOrEmpty(parsed.model_url))
            {
                fail?.Invoke("Backend did not return a model");
                yield break;
            }
            ok?.Invoke(parsed);
        }

        public IEnumerator DownloadFile(string relativeUrl, string destPath, Action<bool, string> done)
        {
            using var req = UnityWebRequest.Get(Url(relativeUrl));
            req.timeout = TimeoutSeconds;
            req.downloadHandler = new DownloadHandlerFile(destPath);
            yield return req.SendWebRequest();
            done(req.result == UnityWebRequest.Result.Success, req.error);
        }

        public IEnumerator UploadSound(string modelId, byte[] wav, Action<bool> done)
        {
            var form = new WWWForm();
            form.AddBinaryData("file", wav, "recording.wav", "audio/wav");
            using var req = UnityWebRequest.Post(Url("/pet-assets/" + modelId + "/sounds"), form);
            req.timeout = 60;
            yield return req.SendWebRequest();
            done(req.result == UnityWebRequest.Result.Success);
        }

        public IEnumerator LabelSound(string modelId, int clipId, string label, Action<bool> done)
        {
            var body = Encoding.UTF8.GetBytes("{\"label\":\"" + label + "\"}");
            using var req = new UnityWebRequest(Url("/pet-assets/" + modelId + "/sounds/" + clipId), "PATCH");
            req.uploadHandler = new UploadHandlerRaw(body);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");
            req.timeout = 30;
            yield return req.SendWebRequest();
            done(req.result == UnityWebRequest.Result.Success);
        }

        public IEnumerator FetchSounds(string modelId, Action<SoundClipDto[]> done)
        {
            using var req = UnityWebRequest.Get(Url("/pet-assets/" + modelId + "/sounds"));
            req.timeout = 30;
            yield return req.SendWebRequest();
            if (req.result != UnityWebRequest.Result.Success)
            {
                done(Array.Empty<SoundClipDto>());
                yield break;
            }
            try
            {
                done(JsonConvert.DeserializeObject<SoundClipDto[]>(req.downloadHandler.text) ?? Array.Empty<SoundClipDto>());
            }
            catch
            {
                done(Array.Empty<SoundClipDto>());
            }
        }

        public IEnumerator UploadVideo(string modelId, string action, byte[] bytes, string filename, Action<VideoMotionResponse, string> done)
        {
            var form = new WWWForm();
            form.AddField("action", action);
            form.AddBinaryData("file", bytes, filename, "video/mp4");
            using var req = UnityWebRequest.Post(Url("/pet-assets/" + modelId + "/videos"), form);
            req.timeout = TimeoutSeconds;
            yield return req.SendWebRequest();
            if (req.result != UnityWebRequest.Result.Success)
            {
                done(null, req.downloadHandler != null && !string.IsNullOrEmpty(req.downloadHandler.text)
                    ? req.downloadHandler.text
                    : req.error);
                yield break;
            }
            try
            {
                done(JsonConvert.DeserializeObject<VideoMotionResponse>(req.downloadHandler.text), null);
            }
            catch (Exception ex)
            {
                done(null, ex.Message);
            }
        }

        public string Url(string path)
        {
            var root = BackendUrl.TrimEnd('/');
            if (!path.StartsWith("/")) path = "/" + path;
            return root + path;
        }
    }
}
