# Sample configuration file for Instant Meshes addon

# Path to the Instant Meshes executable
# Replace with the actual path to your Instant Meshes executable
EXECUTABLE_PATH = "/path/to/instant-meshes/Instant Meshes"

# Default remeshing settings
DEFAULT_SETTINGS = {
    "target_count_type": "FACES",  # "FACES" or "VERTICES"
    "face_count": 5000,
    "vertex_count": 5000,
    "preserve_sharp": True,
    "align_to_boundaries": True,
    "deterministic": False,
    "crease_angle": 30.0,
}

# Advanced settings (not currently implemented in the addon)
ADVANCED_SETTINGS = {
    "smoothing_iterations": 2,
    "field_smoothing": True,
    "knn_points": 10
}