using System;
using System.IO;
using System.Reflection;
using UnityEngine;

namespace PetSoul
{
    /// <summary>
    /// Camera and album via Yasirkula NativeCamera / NativeGallery when those
    /// packages are installed. Reflection keeps this project compiling before
    /// the OpenUPM packages are added.
    /// </summary>
    public class PhotoCapture : MonoBehaviour
    {
        public const int MaxEdge = 1920;
        public const int JpegQuality = 85;

        public void TakePhoto(Action<byte[]> ok, Action<string> fail)
        {
            var type = Type.GetType("NativeCamera, Assembly-CSharp")
                       ?? Type.GetType("NativeCamera, NativeCamera.Runtime");
            if (type == null)
            {
                fail("NativeCamera is not installed. Add com.yasirkula.nativecamera from OpenUPM.");
                return;
            }
            var method = type.GetMethod("TakePicture", new[] { typeof(Action<string>), typeof(int), typeof(bool), typeof(string) });
            if (method == null)
            {
                fail("NativeCamera.TakePicture was not found.");
                return;
            }
            Action<string> callback = path => FinishPath(path, ok, fail);
            method.Invoke(null, new object[] { callback, MaxEdge, true, "" });
        }

        public void PickPhoto(Action<byte[]> ok, Action<string> fail)
        {
            var type = Type.GetType("NativeGallery, Assembly-CSharp")
                       ?? Type.GetType("NativeGallery, NativeGallery.Runtime");
            if (type == null)
            {
                fail("NativeGallery is not installed. Add com.yasirkula.nativegallery from OpenUPM.");
                return;
            }
            var method = type.GetMethod("GetImageFromGallery", new[] { typeof(Action<string>), typeof(string), typeof(string) });
            if (method == null)
            {
                fail("NativeGallery.GetImageFromGallery was not found.");
                return;
            }
            Action<string> callback = path => FinishPath(path, ok, fail);
            method.Invoke(null, new object[] { callback, "Choose a pet photo", "image/*" });
        }

        public void PickVideo(Action<string> ok, Action<string> fail)
        {
            var type = Type.GetType("NativeGallery, Assembly-CSharp")
                       ?? Type.GetType("NativeGallery, NativeGallery.Runtime");
            if (type == null)
            {
                fail("NativeGallery is not installed.");
                return;
            }
            MethodInfo method = null;
            foreach (var candidate in type.GetMethods())
            {
                if (candidate.Name == "GetVideoFromGallery")
                {
                    method = candidate;
                    break;
                }
            }
            if (method == null)
            {
                fail("NativeGallery.GetVideoFromGallery was not found.");
                return;
            }
            var parameters = method.GetParameters();
            Action<string> callback = path =>
            {
                if (string.IsNullOrEmpty(path)) fail("Video pick cancelled.");
                else ok(path);
            };
            var args = new object[parameters.Length];
            args[0] = callback;
            if (parameters.Length > 1) args[1] = "Choose a dog video";
            if (parameters.Length > 2) args[2] = "video/*";
            method.Invoke(null, args);
        }

        static void FinishPath(string path, Action<byte[]> ok, Action<string> fail)
        {
            if (string.IsNullOrEmpty(path) || !File.Exists(path))
            {
                fail("Photo cancelled.");
                return;
            }
            try
            {
                ok(Compress(File.ReadAllBytes(path)));
            }
            catch (Exception ex)
            {
                fail(ex.Message);
            }
        }

        public static byte[] Compress(byte[] encoded)
        {
            var tex = new Texture2D(2, 2, TextureFormat.RGB24, false);
            if (!tex.LoadImage(encoded))
            {
                UnityEngine.Object.Destroy(tex);
                throw new InvalidOperationException("Could not read that image.");
            }
            var src = tex;
            var edge = Mathf.Max(tex.width, tex.height);
            if (edge > MaxEdge)
            {
                var scale = MaxEdge / (float)edge;
                src = Scale(tex, Mathf.RoundToInt(tex.width * scale), Mathf.RoundToInt(tex.height * scale));
                UnityEngine.Object.Destroy(tex);
            }
            var jpg = src.EncodeToJPG(JpegQuality);
            UnityEngine.Object.Destroy(src);
            return jpg;
        }

        static Texture2D Scale(Texture2D src, int width, int height)
        {
            var rt = RenderTexture.GetTemporary(width, height);
            Graphics.Blit(src, rt);
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var dst = new Texture2D(width, height, TextureFormat.RGB24, false);
            dst.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            dst.Apply();
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
            return dst;
        }
    }
}
