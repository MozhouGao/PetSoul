using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

namespace PetSoul
{
    public static class UIFactory
    {
        public static Font Font => Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

        public static RectTransform Panel(Transform parent, string name)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(CanvasRenderer), typeof(Image));
            var rect = go.GetComponent<RectTransform>();
            rect.SetParent(parent, false);
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.offsetMin = Vector2.zero;
            rect.offsetMax = Vector2.zero;
            go.GetComponent<Image>().color = new Color(0.96f, 0.94f, 0.90f, 1f);
            return rect;
        }

        public static Button Button(Transform parent, string label, Vector2 anchor, Vector2 size, UnityAction onClick)
        {
            var go = new GameObject(label, typeof(RectTransform), typeof(CanvasRenderer), typeof(Image), typeof(Button));
            var rect = go.GetComponent<RectTransform>();
            rect.SetParent(parent, false);
            rect.anchorMin = anchor;
            rect.anchorMax = anchor;
            rect.sizeDelta = size;
            rect.anchoredPosition = Vector2.zero;
            go.GetComponent<Image>().color = new Color(0.20f, 0.45f, 0.32f, 1f);
            go.GetComponent<Button>().onClick.AddListener(onClick);
            Text(go.transform, label, 22, Color.white);
            return go.GetComponent<Button>();
        }

        public static Text Text(Transform parent, string value, int size, Color color)
        {
            var go = new GameObject("Text", typeof(RectTransform), typeof(CanvasRenderer), typeof(Text));
            var rect = go.GetComponent<RectTransform>();
            rect.SetParent(parent, false);
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.offsetMin = new Vector2(8, 4);
            rect.offsetMax = new Vector2(-8, -4);
            var text = go.GetComponent<Text>();
            text.font = Font;
            text.fontSize = size;
            text.alignment = TextAnchor.MiddleCenter;
            text.color = color;
            text.text = value;
            text.horizontalOverflow = HorizontalWrapMode.Wrap;
            text.verticalOverflow = VerticalWrapMode.Overflow;
            return text;
        }

        public static InputField Field(Transform parent, string placeholder, Vector2 anchor)
        {
            var go = new GameObject("Field", typeof(RectTransform), typeof(CanvasRenderer), typeof(Image), typeof(InputField));
            var rect = go.GetComponent<RectTransform>();
            rect.SetParent(parent, false);
            rect.anchorMin = anchor;
            rect.anchorMax = anchor;
            rect.sizeDelta = new Vector2(640, 56);
            go.GetComponent<Image>().color = Color.white;
            var text = Text(go.transform, "", 20, Color.black);
            text.alignment = TextAnchor.MiddleLeft;
            var field = go.GetComponent<InputField>();
            field.textComponent = text;
            field.text = placeholder;
            return field;
        }
    }
}
