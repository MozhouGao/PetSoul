using System;
using System.Collections.Generic;
using UnityEngine;

namespace PetSoul
{
    /// <summary>
    /// Plays idle, walk, run, sit, stand, and stretch with a 0.2s crossfade.
    /// Legacy Animation is what glTFast writes for a custom dog skeleton.
    /// </summary>
    public class DogMotionPlayer : MonoBehaviour
    {
        public const float Fade = 0.2f;
        public static readonly string[] States = { "idle", "walk", "run", "sit", "stand", "stretch" };

        Animation _legacy;
        Animator _animator;
        string _current = "idle";

        public event Action<string> StateChanged;

        public bool HasClips => _legacy != null || _animator != null;

        public void Bind(GameObject root)
        {
            _legacy = root.GetComponentInChildren<Animation>();
            _animator = root.GetComponentInChildren<Animator>();
            if (_legacy != null)
            {
                _legacy.playAutomatically = false;
                _legacy.wrapMode = WrapMode.Loop;
                Play("idle");
            }
            else if (_animator != null)
            {
                _animator.CrossFade("idle", Fade);
                _current = "idle";
                StateChanged?.Invoke(_current);
            }
        }

        public void Play(string state)
        {
            if (string.IsNullOrEmpty(state)) return;
            if (_legacy != null)
            {
                if (_legacy.GetClip(state) == null) return;
                _legacy.CrossFade(state, Fade);
            }
            else if (_animator != null)
            {
                _animator.CrossFade(state, Fade);
            }
            else return;
            _current = state;
            StateChanged?.Invoke(state);
        }

        public List<string> Available()
        {
            var names = new List<string>();
            if (_legacy == null) return names;
            foreach (AnimationState state in _legacy)
                names.Add(state.name);
            return names;
        }
    }
}
