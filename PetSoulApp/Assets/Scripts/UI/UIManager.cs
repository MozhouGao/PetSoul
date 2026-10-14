using System.Collections;
using System.IO;
using System.Text;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.UI;

namespace PetSoul
{
    public class UIManager : MonoBehaviour
    {
        PetSoulAPI _api;
        PhotoCapture _photos;
        ModelStorage _storage;
        ModelViewer _viewer;
        DogMotionPlayer _motion;
        DogAudioPlayer _audio;
        Camera _camera;

        RectTransform _home;
        RectTransform _processing;
        RectTransform _viewerScreen;
        RectTransform _gallery;
        RectTransform _confirm;

        Text _health;
        Text _status;
        Text _profile;
        InputField _url;
        SavedModel _current;
        string _pendingDelete;
        string _videoAction = "walk";
        bool _recording;
        AudioClip _micClip;

        public void Init(Transform canvas, PetSoulAPI api, PhotoCapture photos, ModelStorage storage,
            ModelViewer viewer, DogMotionPlayer motion, DogAudioPlayer audio, Camera camera)
        {
            _api = api;
            _photos = photos;
            _storage = storage;
            _viewer = viewer;
            _motion = motion;
            _audio = audio;
            _camera = camera;

            _home = BuildHome(canvas);
            _processing = BuildProcessing(canvas);
            _viewerScreen = BuildViewer(canvas);
            _gallery = BuildGallery(canvas);
            _confirm = BuildConfirm(canvas);
            Show(_home);
            StartCoroutine(RefreshHealth());
        }

        RectTransform BuildHome(Transform canvas)
        {
            var panel = UIFactory.Panel(canvas, "Home");
            UIFactory.Text(panel, "Pet Soul", 48, new Color(0.15f, 0.15f, 0.15f)).rectTransform.anchorMin = new Vector2(0, 0.82f);
            _health = UIFactory.Text(panel, "Server …", 22, Color.gray);
            _health.rectTransform.anchorMin = new Vector2(0.1f, 0.74f);
            _health.rectTransform.anchorMax = new Vector2(0.9f, 0.80f);
            _url = UIFactory.Field(panel, _api.BackendUrl, new Vector2(0.5f, 0.68f));
            _url.onEndEdit.AddListener(value =>
            {
                _api.BackendUrl = value.Trim();
                PlayerPrefs.SetString("petsoul.backend", _api.BackendUrl);
                StartCoroutine(RefreshHealth());
            });
            UIFactory.Button(panel, "Take Photo", new Vector2(0.5f, 0.52f), new Vector2(520, 80), () =>
                _photos.TakePhoto(BeginGenerate, ShowError));
            UIFactory.Button(panel, "Choose from Album", new Vector2(0.5f, 0.42f), new Vector2(520, 80), () =>
                _photos.PickPhoto(BeginGenerate, ShowError));
            UIFactory.Button(panel, "My Models", new Vector2(0.5f, 0.32f), new Vector2(520, 80), ShowGallery);
            return panel;
        }

        RectTransform BuildProcessing(Transform canvas)
        {
            var panel = UIFactory.Panel(canvas, "Processing");
            _status = UIFactory.Text(panel, "", 28, Color.black);
            UIFactory.Button(panel, "Cancel", new Vector2(0.5f, 0.2f), new Vector2(320, 70), () =>
            {
                StopAllCoroutines();
                Show(_home);
            });
            return panel;
        }

        RectTransform BuildViewer(Transform canvas)
        {
            var panel = UIFactory.Panel(canvas, "Viewer");
            panel.GetComponent<Image>().color = new Color(0, 0, 0, 0.01f);
            _profile = UIFactory.Text(panel, "", 20, Color.black);
            _profile.rectTransform.anchorMin = new Vector2(0.05f, 0.86f);
            _profile.rectTransform.anchorMax = new Vector2(0.95f, 0.98f);
            UIFactory.Button(panel, "Sit", new Vector2(0.18f, 0.16f), new Vector2(150, 64), () => _motion.Play("sit"));
            UIFactory.Button(panel, "Run", new Vector2(0.38f, 0.16f), new Vector2(150, 64), () => _motion.Play("run"));
            UIFactory.Button(panel, "Stretch", new Vector2(0.58f, 0.16f), new Vector2(180, 64), () => _motion.Play("stretch"));
            UIFactory.Button(panel, "Bark", new Vector2(0.80f, 0.16f), new Vector2(150, 64), () => _audio.Bark());
            UIFactory.Button(panel, "Record", new Vector2(0.22f, 0.08f), new Vector2(180, 58), ToggleRecord);
            UIFactory.Button(panel, "Walk video", new Vector2(0.48f, 0.08f), new Vector2(180, 58), () => UploadMotion("walk"));
            UIFactory.Button(panel, "Sit video", new Vector2(0.68f, 0.08f), new Vector2(160, 58), () => UploadMotion("sit"));
            UIFactory.Button(panel, "Stretch video", new Vector2(0.88f, 0.08f), new Vector2(200, 58), () => UploadMotion("stretch"));
            UIFactory.Button(panel, "Back", new Vector2(0.12f, 0.94f), new Vector2(140, 52), () => Show(_home));
            return panel;
        }

        RectTransform BuildGallery(Transform canvas)
        {
            var panel = UIFactory.Panel(canvas, "Gallery");
            UIFactory.Text(panel, "My Models", 36, Color.black).rectTransform.anchorMin = new Vector2(0, 0.90f);
            UIFactory.Button(panel, "Back", new Vector2(0.5f, 0.06f), new Vector2(320, 64), () => Show(_home));
            return panel;
        }

        RectTransform BuildConfirm(Transform canvas)
        {
            var panel = UIFactory.Panel(canvas, "Confirm");
            panel.GetComponent<Image>().color = new Color(0, 0, 0, 0.45f);
            UIFactory.Text(panel, "Delete this model?", 32, Color.white);
            UIFactory.Button(panel, "Delete", new Vector2(0.35f, 0.4f), new Vector2(220, 70), () =>
            {
                if (!string.IsNullOrEmpty(_pendingDelete)) _storage.Delete(_pendingDelete);
                _pendingDelete = null;
                ShowGallery();
            });
            UIFactory.Button(panel, "Keep", new Vector2(0.65f, 0.4f), new Vector2(220, 70), ShowGallery);
            return panel;
        }

        void BeginGenerate(byte[] jpeg)
        {
            Show(_processing);
            StartCoroutine(GenerateRoutine(jpeg));
        }

        IEnumerator GenerateRoutine(byte[] jpeg)
        {
            GenerateResponse response = null;
            string error = null;
            yield return _api.Generate(jpeg, text => _status.text = text, r => response = r, e => error = e);
            if (error != null || response == null)
            {
                _status.text = error ?? "Generation failed";
                UIFactory.Button(_processing, "Retry", new Vector2(0.5f, 0.32f), new Vector2(320, 70), () => BeginGenerate(jpeg));
                yield break;
            }
            _status.text = "Downloading model...";
            var tempGlb = Path.Combine(Application.temporaryCachePath, response.filename);
            var ok = false;
            yield return _api.DownloadFile(response.model_url, tempGlb, (success, _) => ok = success);
            if (!ok)
            {
                _status.text = "Download failed";
                yield break;
            }
            var glb = File.ReadAllBytes(tempGlb);
            byte[] rigged = null;
            if (!string.IsNullOrEmpty(response.rigged_model_url))
            {
                var tempRig = Path.Combine(Application.temporaryCachePath, "rigged_" + response.filename);
                var rigOk = false;
                yield return _api.DownloadFile(response.rigged_model_url, tempRig, (success, _) => rigOk = success);
                if (rigOk) rigged = File.ReadAllBytes(tempRig);
            }
            _current = _storage.Save(response, glb, rigged, null);
            yield return ShowModel(_current);
        }

        IEnumerator ShowModel(SavedModel entry)
        {
            _current = entry;
            Show(_viewerScreen);
            var path = _storage.PreferredGlb(entry);
            string error = null;
            yield return _viewer.Load(path, e => error = e);
            if (error != null)
            {
                _profile.text = error;
                yield break;
            }
            PetProfile profile = null;
            try { profile = JsonConvert.DeserializeObject<PetProfile>(entry.profileJson ?? ""); }
            catch { /* overlay stays empty */ }
            _profile.text = Describe(profile);
            var png = _viewer.CaptureThumbnail(_camera);
            if (png != null) _storage.UpdateThumbnail(entry, png);
            if (!string.IsNullOrEmpty(entry.modelId))
                yield return LoadSounds(entry.modelId);
        }

        IEnumerator LoadSounds(string modelId)
        {
            SoundClipDto[] clips = null;
            yield return _api.FetchSounds(modelId, list => clips = list);
            _audio.Clear();
            if (clips == null) yield break;
            foreach (var clip in clips)
            {
                if (clip.label == "other") continue;
                using var req = UnityEngine.Networking.UnityWebRequestMultimedia.GetAudioClip(_api.Url(clip.url), AudioType.WAV);
                yield return req.SendWebRequest();
                if (req.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
                    _audio.Add(clip.label, UnityEngine.Networking.DownloadHandlerAudioClip.GetContent(req));
            }
        }

        void ShowGallery()
        {
            Show(_gallery);
            for (var i = _gallery.childCount - 1; i >= 0; i--)
            {
                var child = _gallery.GetChild(i);
                if (child.name.StartsWith("Row")) Destroy(child.gameObject);
            }
            var models = _storage.LoadAll();
            for (var i = 0; i < models.Count; i++)
            {
                var entry = models[i];
                var y = 0.82f - i * 0.12f;
                var label = string.IsNullOrEmpty(entry.breed) ? entry.modelId : entry.breed;
                UIFactory.Button(_gallery, string.IsNullOrEmpty(label) ? "Pet" : label, new Vector2(0.38f, y), new Vector2(420, 70),
                    () => StartCoroutine(ShowModel(entry))).gameObject.name = "Row" + i;
                UIFactory.Button(_gallery, "Delete", new Vector2(0.82f, y), new Vector2(160, 70), () =>
                {
                    _pendingDelete = entry.id;
                    Show(_confirm);
                }).gameObject.name = "RowDel" + i;
            }
        }

        void ToggleRecord()
        {
            if (_current == null || string.IsNullOrEmpty(_current.modelId)) return;
            if (!_recording)
            {
                _micClip = Microphone.Start(null, false, 5, 44100);
                _recording = true;
                _profile.text = "Recording 5 seconds…";
                StartCoroutine(StopRecordAfter());
            }
        }

        IEnumerator StopRecordAfter()
        {
            yield return new WaitForSeconds(5f);
            var pos = Microphone.GetPosition(null);
            Microphone.End(null);
            _recording = false;
            if (_micClip == null) yield break;
            var samples = new float[pos * _micClip.channels];
            _micClip.GetData(samples, 0);
            var wav = WavEncoder.FromFloats(samples, _micClip.frequency, _micClip.channels);
            var uploaded = false;
            yield return _api.UploadSound(_current.modelId, wav, ok => uploaded = ok);
            _profile.text = uploaded
                ? "Saved. Label the clip bark, whine, or pant on the server, then reopen."
                : "Could not upload the recording.";
        }

        void UploadMotion(string action)
        {
            if (_current == null) return;
            _videoAction = action;
            _photos.PickVideo(path => StartCoroutine(SendVideo(path)), ShowError);
        }

        IEnumerator SendVideo(string path)
        {
            var bytes = File.ReadAllBytes(path);
            VideoMotionResponse response = null;
            string error = null;
            yield return _api.UploadVideo(_current.modelId, _videoAction, bytes, Path.GetFileName(path), (r, e) =>
            {
                response = r;
                error = e;
            });
            if (error != null || response == null || string.IsNullOrEmpty(response.rigged_model_url))
            {
                _profile.text = error ?? "Could not learn motion from that video.";
                yield break;
            }
            var dest = Path.Combine(Application.temporaryCachePath, "owner_rigged.glb");
            var ok = false;
            yield return _api.DownloadFile(response.rigged_model_url, dest, (success, _) => ok = success);
            if (!ok) yield break;
            var data = File.ReadAllBytes(dest);
            _storage.UpdateRigged(_current, data);
            _profile.text = "Using your " + _videoAction + " video (" + response.keypoint_source + ").";
            yield return ShowModel(_current);
        }

        IEnumerator RefreshHealth()
        {
            var healthy = false;
            yield return _api.CheckHealth(ok => healthy = ok);
            if (_health != null)
            {
                _health.text = healthy ? "● Server ready" : "● Server unreachable";
                _health.color = healthy ? new Color(0.1f, 0.55f, 0.25f) : new Color(0.7f, 0.15f, 0.15f);
            }
        }

        void ShowError(string message)
        {
            Show(_processing);
            _status.text = message;
        }

        void Show(RectTransform screen)
        {
            _home.gameObject.SetActive(screen == _home);
            _processing.gameObject.SetActive(screen == _processing);
            _viewerScreen.gameObject.SetActive(screen == _viewerScreen);
            _gallery.gameObject.SetActive(screen == _gallery);
            _confirm.gameObject.SetActive(screen == _confirm);
        }

        static string Describe(PetProfile profile)
        {
            if (profile == null) return "";
            var colors = profile.coat_colors != null ? string.Join(", ", profile.coat_colors) : "";
            var marks = profile.markings != null ? string.Join(", ", profile.markings) : "";
            var builder = new StringBuilder();
            builder.Append(profile.breed ?? profile.species ?? "Dog");
            if (!string.IsNullOrEmpty(colors)) builder.Append("\n").Append(colors);
            if (!string.IsNullOrEmpty(marks)) builder.Append("\n").Append(marks);
            return builder.ToString();
        }
    }

    public static class WavEncoder
    {
        public static byte[] FromFloats(float[] samples, int sampleRate, int channels)
        {
            channels = Mathf.Max(channels, 1);
            var mono = new float[samples.Length / channels];
            for (var i = 0; i < mono.Length; i++)
            {
                float sum = 0f;
                for (var c = 0; c < channels; c++) sum += samples[i * channels + c];
                mono[i] = sum / channels;
            }
            var data = new byte[mono.Length * 2];
            for (var i = 0; i < mono.Length; i++)
            {
                var s = (short)Mathf.Clamp(mono[i] * 32767f, short.MinValue, short.MaxValue);
                data[i * 2] = (byte)(s & 0xff);
                data[i * 2 + 1] = (byte)((s >> 8) & 0xff);
            }
            using var stream = new MemoryStream();
            using var writer = new BinaryWriter(stream);
            writer.Write(Encoding.ASCII.GetBytes("RIFF"));
            writer.Write(36 + data.Length);
            writer.Write(Encoding.ASCII.GetBytes("WAVEfmt "));
            writer.Write(16);
            writer.Write((short)1);
            writer.Write((short)1);
            writer.Write(sampleRate);
            writer.Write(sampleRate * 2);
            writer.Write((short)2);
            writer.Write((short)16);
            writer.Write(Encoding.ASCII.GetBytes("data"));
            writer.Write(data.Length);
            writer.Write(data);
            return stream.ToArray();
        }
    }
}
