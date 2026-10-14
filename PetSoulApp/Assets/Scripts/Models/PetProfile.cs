using System;

namespace PetSoul
{
    [Serializable]
    public class PetProfile
    {
        public string species;
        public string breed;
        public float breed_confidence;
        public string[] coat_colors;
        public string[] markings;
        public string fur_length;
    }

    [Serializable]
    public class GenerateResponse
    {
        public bool success;
        public PetProfile profile;
        public string texture_prompt;
        public string model_url;
        public string filename;
        public string model_id;
        public string rigged_model_url;
        public string[] animation_clips;
    }

    [Serializable]
    public class HealthResponse
    {
        public string status;
        public bool pipeline_ready;
    }

    [Serializable]
    public class SoundClipDto
    {
        public int id;
        public string model_id;
        public string label;
        public float duration;
        public string url;
    }

    [Serializable]
    public class VideoMotionResponse
    {
        public string model_id;
        public string keypoint_source;
        public string[] replaced_presets;
        public string rigged_model_url;
    }
}
