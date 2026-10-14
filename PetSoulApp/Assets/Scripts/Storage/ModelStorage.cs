using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;
using UnityEngine;

namespace PetSoul
{
    [Serializable]
    public class SavedModel
    {
        public string id;
        public string modelId;
        public string glbPath;
        public string riggedGlbPath;
        public string profileJson;
        public string createdAt;
        public string thumbnailPath;
        public string breed;
    }

    public class ModelStorage : MonoBehaviour
    {
        string Root => Path.Combine(Application.persistentDataPath, "petsoul");
        string IndexPath => Path.Combine(Root, "index.json");

        public void Ensure()
        {
            Directory.CreateDirectory(Root);
        }

        public List<SavedModel> LoadAll()
        {
            Ensure();
            if (!File.Exists(IndexPath)) return new List<SavedModel>();
            try
            {
                return JsonConvert.DeserializeObject<List<SavedModel>>(File.ReadAllText(IndexPath)) ?? new List<SavedModel>();
            }
            catch
            {
                return new List<SavedModel>();
            }
        }

        public SavedModel Save(GenerateResponse response, byte[] glb, byte[] riggedOrNull, byte[] thumbnailPng)
        {
            Ensure();
            var id = Guid.NewGuid().ToString("N");
            var dir = Path.Combine(Root, id);
            Directory.CreateDirectory(dir);
            var glbPath = Path.Combine(dir, "model.glb");
            File.WriteAllBytes(glbPath, glb);
            var entry = new SavedModel
            {
                id = id,
                modelId = response.model_id,
                glbPath = glbPath,
                profileJson = JsonConvert.SerializeObject(response.profile),
                createdAt = DateTime.UtcNow.ToString("o"),
                breed = response.profile != null ? response.profile.breed : "",
            };
            if (riggedOrNull != null && riggedOrNull.Length > 0)
            {
                entry.riggedGlbPath = Path.Combine(dir, "rigged.glb");
                File.WriteAllBytes(entry.riggedGlbPath, riggedOrNull);
            }
            if (thumbnailPng != null && thumbnailPng.Length > 0)
            {
                entry.thumbnailPath = Path.Combine(dir, "thumb.png");
                File.WriteAllBytes(entry.thumbnailPath, thumbnailPng);
            }
            var all = LoadAll();
            all.Insert(0, entry);
            File.WriteAllText(IndexPath, JsonConvert.SerializeObject(all, Formatting.Indented));
            return entry;
        }

        public void UpdateThumbnail(SavedModel entry, byte[] png)
        {
            if (entry == null || png == null) return;
            entry.thumbnailPath = Path.Combine(Root, entry.id, "thumb.png");
            File.WriteAllBytes(entry.thumbnailPath, png);
            Replace(entry);
        }

        public void UpdateRigged(SavedModel entry, byte[] glb)
        {
            if (entry == null || glb == null) return;
            entry.riggedGlbPath = Path.Combine(Root, entry.id, "rigged.glb");
            File.WriteAllBytes(entry.riggedGlbPath, glb);
            Replace(entry);
        }

        public void Delete(string id)
        {
            var all = LoadAll();
            var found = all.Find(m => m.id == id);
            if (found != null)
            {
                var dir = Path.Combine(Root, found.id);
                if (Directory.Exists(dir)) Directory.Delete(dir, true);
                all.RemoveAll(m => m.id == id);
                File.WriteAllText(IndexPath, JsonConvert.SerializeObject(all, Formatting.Indented));
            }
        }

        void Replace(SavedModel entry)
        {
            var all = LoadAll();
            var index = all.FindIndex(m => m.id == entry.id);
            if (index >= 0) all[index] = entry;
            else all.Insert(0, entry);
            File.WriteAllText(IndexPath, JsonConvert.SerializeObject(all, Formatting.Indented));
        }

        public string PreferredGlb(SavedModel entry)
        {
            if (entry == null) return null;
            if (!string.IsNullOrEmpty(entry.riggedGlbPath) && File.Exists(entry.riggedGlbPath))
                return entry.riggedGlbPath;
            return entry.glbPath;
        }
    }
}
