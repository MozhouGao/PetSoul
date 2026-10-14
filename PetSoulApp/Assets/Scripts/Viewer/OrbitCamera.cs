using UnityEngine;

namespace PetSoul
{
    public class OrbitCamera : MonoBehaviour
    {
        public Transform Target;
        public float Distance = 3f;
        public float Yaw = 25f;
        public float Pitch = 15f;
        public float MinDistance = 0.4f;
        public float MaxDistance = 12f;

        Vector3 _pan;
        Vector2 _lastSingle;
        float _lastPinch;
        bool _pinching;

        public void Frame(Bounds bounds)
        {
            Target = null;
            _pan = bounds.center;
            Distance = Mathf.Clamp(bounds.extents.magnitude * 2.2f, MinDistance, MaxDistance);
            Yaw = 25f;
            Pitch = 15f;
            Apply();
        }

        void LateUpdate()
        {
            var touches = Input.touches;
            if (touches.Length == 1)
            {
                var t = touches[0];
                if (t.phase == TouchPhase.Moved)
                {
                    var delta = t.position - _lastSingle;
                    Yaw += delta.x * 0.4f;
                    Pitch = Mathf.Clamp(Pitch - delta.y * 0.25f, -10f, 80f);
                }
                _lastSingle = t.position;
                _pinching = false;
            }
            else if (touches.Length >= 2)
            {
                var dist = Vector2.Distance(touches[0].position, touches[1].position);
                var mid = (touches[0].position + touches[1].position) * 0.5f;
                if (!_pinching)
                {
                    _lastPinch = dist;
                    _lastSingle = mid;
                    _pinching = true;
                }
                else
                {
                    Distance = Mathf.Clamp(Distance * (_lastPinch / Mathf.Max(dist, 1f)), MinDistance, MaxDistance);
                    var delta = mid - _lastSingle;
                    var right = transform.right;
                    var up = transform.up;
                    _pan -= (right * delta.x + up * delta.y) * Distance * 0.0015f;
                    _lastPinch = dist;
                    _lastSingle = mid;
                }
            }
            else
            {
                _pinching = false;
                if (Input.GetMouseButton(0))
                {
                    Yaw += Input.GetAxis("Mouse X") * 4f;
                    Pitch = Mathf.Clamp(Pitch - Input.GetAxis("Mouse Y") * 2f, -10f, 80f);
                }
                Distance = Mathf.Clamp(Distance - Input.mouseScrollDelta.y * 0.25f, MinDistance, MaxDistance);
            }
            Apply();
        }

        void Apply()
        {
            var rot = Quaternion.Euler(Pitch, Yaw, 0f);
            var focus = Target != null ? Target.position : _pan;
            transform.position = focus + rot * new Vector3(0f, 0f, -Distance);
            transform.rotation = rot;
        }
    }
}
