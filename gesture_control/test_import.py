"""
Simple test script to verify gesture control module installation.
This tests if all dependencies are properly installed without requiring a webcam.
"""

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing module imports...")

    try:
        import cv2
        print("✓ OpenCV imported successfully")
        print(f"  OpenCV version: {cv2.__version__}")
    except ImportError as e:
        print(f"✗ Failed to import OpenCV: {e}")
        return False

    try:
        import mediapipe as mp
        print("✓ MediaPipe imported successfully")
        print(f"  MediaPipe version: {mp.__version__}")
    except ImportError as e:
        print(f"✗ Failed to import MediaPipe: {e}")
        return False

    try:
        import numpy as np
        print("✓ NumPy imported successfully")
        print(f"  NumPy version: {np.__version__}")
    except ImportError as e:
        print(f"✗ Failed to import NumPy: {e}")
        return False

    try:
        from gesture_control import HandTracker
        print("✓ HandTracker imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import HandTracker: {e}")
        return False

    print("\n✓ All imports successful!")
    return True


def test_hand_tracker_initialization():
    """Test if HandTracker can be initialized."""
    print("\nTesting HandTracker initialization...")

    try:
        from gesture_control import HandTracker
        tracker = HandTracker(max_hands=2)
        print("✓ HandTracker initialized successfully")
        tracker.release()
        print("✓ HandTracker released successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize HandTracker: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Gesture Control Module - Import Test")
    print("=" * 60)
    print()

    all_passed = True

    # Test imports
    if not test_imports():
        all_passed = False

    # Test initialization
    if not test_hand_tracker_initialization():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("\nYou can now run the hand tracking application:")
        print("  python gesture_control/hand_tracker.py")
    else:
        print("✗ Some tests failed!")
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements.txt")
    print("=" * 60)


if __name__ == "__main__":
    main()
