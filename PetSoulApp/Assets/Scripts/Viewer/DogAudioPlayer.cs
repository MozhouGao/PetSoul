using System.Collections.Generic;
using UnityEngine;

namespace PetSoul
{
    /// <summary>
    /// Plays the pet's own recordings. Idle and run pant, sit and stretch whine,
    /// and a tap plays a bark. Takes are shuffled so the same file does not repeat.
    /// </summary>
    public class DogAudioPlayer : MonoBehaviour
    {
        AudioSource _source;
        readonly Dictionary<string, List<AudioClip>> _bank = new Dictionary<string, List<AudioClip>>();
        readonly Dictionary<string, int> _last = new Dictionary<string, int>();

        void Awake()
        {
            _source = gameObject.AddComponent<AudioSource>();
            _source.playOnAwake = false;
            _source.spatialBlend = 0f;
        }

        public void Bind(DogMotionPlayer motion)
        {
            motion.StateChanged += OnState;
        }

        public void Add(string label, AudioClip clip)
        {
            if (clip == null || string.IsNullOrEmpty(label)) return;
            if (!_bank.TryGetValue(label, out var list))
            {
                list = new List<AudioClip>();
                _bank[label] = list;
            }
            list.Add(clip);
        }

        public void Clear()
        {
            _bank.Clear();
            _last.Clear();
        }

        public void Bark() => PlayLabel("bark");

        void OnState(string state)
        {
            if (state == "idle" || state == "run" || state == "walk") PlayLabel("pant");
            else if (state == "sit" || state == "stretch" || state == "stand") PlayLabel("whine");
        }

        void PlayLabel(string label)
        {
            if (!_bank.TryGetValue(label, out var list) || list.Count == 0) return;
            var index = 0;
            if (list.Count == 1)
            {
                index = 0;
            }
            else
            {
                var previous = _last.TryGetValue(label, out var last) ? last : -1;
                do { index = Random.Range(0, list.Count); } while (index == previous);
            }
            _last[label] = index;
            _source.clip = list[index];
            _source.loop = label == "pant";
            _source.Play();
        }
    }
}
