"""
Quick Test Script for Pet 3D Model Generator
Run this to quickly test the backend functionality.
Requires the server to be running: python app.py
"""

import requests
import sys
import os
import time

API_URL = "http://localhost:8000"


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_success(text):
    print(f"  PASS  {text}")


def print_error(text):
    print(f"  FAIL  {text}")


def print_info(text):
    print(f"  INFO  {text}")


def test_health():
    print_header("TEST 1: Health Check")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        data = response.json()

        if data.get("status") == "healthy" and data.get("pipeline_ready"):
            print_success("Server is healthy and ready!")
            print_info(f"Detector ready: {data.get('detector_ready')}")
            print_info(f"Generator ready: {data.get('generator_ready')}")
            return True
        else:
            print_error("Server is not fully ready")
            print(data)
            return False
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to server at http://localhost:8000")
        print_info("Make sure the server is running: python app.py")
        return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def test_generate_3d(image_path):
    print_header("TEST 2: Generate 3D Model")
    print_info(f"Image: {image_path}")
    print_info("This will take 1-3 minutes...")

    if not os.path.exists(image_path):
        print_error(f"Image file not found: {image_path}")
        return False

    try:
        with open(image_path, "rb") as f:
            files = {"file": f}
            start_time = time.time()

            response = requests.post(
                f"{API_URL}/generate-3d-model",
                files=files,
                timeout=300,
            )
            elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            profile = data.get("profile", {})

            print_success(f"3D model generated in {elapsed:.1f}s!")

            # Pet profile
            print(f"\n  Breed: {profile.get('breed', 'Unknown')}")
            if profile.get("breed_confidence"):
                print(f"  Confidence: {profile['breed_confidence'] * 100:.1f}%")
            print(f"  Colors: {', '.join(profile.get('coat_colors', []))}")
            markings = profile.get("markings", [])
            print(f"  Markings: {', '.join(markings) if markings else 'None detected'}")
            print(f"  Body: {profile.get('body_type', '-')} | Ears: {profile.get('ear_shape', '-')} | Tail: {profile.get('tail_type', '-')}")
            print(f"  Snout: {profile.get('snout_length', '-')} | Size: {profile.get('size_class', '-')} | Fur: {profile.get('fur_length', '-')}")

            # Texture prompt
            print(f"\n  Texture prompt:")
            print(f"  {data.get('texture_prompt', 'N/A')}")

            # Download link
            print(f"\n  Model: {data.get('filename', 'N/A')}")
            print(f"  URL: {API_URL}{data.get('model_url', '')}")
            print(f"\n  View at: https://gltf-viewer.donmccurdy.com/")

            return True
        else:
            print_error(f"Generation failed: {response.status_code}")
            try:
                error_data = response.json()
                print(error_data.get("detail", response.text))
            except Exception:
                print(response.text)
            return False

    except requests.exceptions.Timeout:
        print_error("Request timed out (took longer than 5 minutes)")
        return False
    except Exception as e:
        print_error(f"Generation error: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("  PET 3D MODEL GENERATOR - QUICK TEST")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\nUsage: python quick_test.py <path_to_pet_image>")
        print("\nExample:")
        print("  python quick_test.py test_dog.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    results = []

    # Test 1: Health Check
    results.append(("Health Check", test_health()))

    if not results[-1][1]:
        print_error("Server is not ready. Start it first: python app.py")
        sys.exit(1)

    # Test 2: Generate 3D Model
    results.append(("Generate 3D Model", test_generate_3d(image_path)))

    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "  PASS" if result else "  FAIL"
        print(f"{status}  {test_name}")

    print(f"\n  Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n  All tests passed!")
        print("  Web interface: http://localhost:8000/test")


if __name__ == "__main__":
    main()
