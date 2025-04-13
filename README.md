# Instant Meshes Blender Addon

A Blender addon that integrates the powerful [Instant Meshes](https://github.com/wjakob/instant-meshes) retopology tool directly into Blender.

## Features

- Remesh your 3D models directly from within Blender
- Control face/vertex count
- Preserve sharp edges and boundaries
- Apply deterministic remeshing for stable results
- Adjust crease angles for controlling feature preservation

## Installation

### Part 1: Installing Instant Meshes on Linux

#### Prerequisites

First, ensure you have the required dependencies:

```bash
sudo apt update
sudo apt install zenity libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev
```

#### Method 1: Download Pre-compiled Binary (Recommended)

1. Download the Linux binary
   ```bash
   wget https://github.com/wjakob/instant-meshes/releases/latest/download/InstantMeshes-Linux.zip
   ```

2. Extract the downloaded file
   ```bash
   unzip InstantMeshes-Linux.zip -d instant-meshes
   ```

3. Make the executable file runnable
   ```bash
   chmod +x instant-meshes/Instant\ Meshes
   ```

4. Note the full path to the executable for later use
   ```bash
   readlink -f instant-meshes/Instant\ Meshes
   ```

#### Method 2: Build from Source

If you prefer to build from source:

1. Clone the GitHub repository and its submodules
   ```bash
   git clone --recursive https://github.com/wjakob/instant-meshes
   cd instant-meshes
   ```

2. Create a build directory and run CMake
   ```bash
   mkdir build
   cd build
   cmake ..
   ```

3. Compile the program
   ```bash
   make -j4
   ```

4. After successful compilation, note the full path to the executable
   ```bash
   readlink -f "build/Instant Meshes"
   ```

### Part 2: Installing the Blender Addon

#### Option 1: Use a pre-packaged release

1. Download the addon from the [Releases page](https://github.com/limbicnation/instant-meshes-blender-addon/releases)

#### Option 2: Package the addon yourself

1. Clone this repository
   ```bash
   git clone https://github.com/limbicnation/instant-meshes-blender-addon.git
   cd instant-meshes-blender-addon
   ```

2. Run the packaging script
   ```bash
   ./package_addon.py
   ```

3. The script will create `instant_meshes_addon.zip` in the repository root

#### Installation Steps

1. Open Blender and go to Edit → Preferences

2. Select the "Add-ons" tab

3. Click the "Install..." button at the top right

4. Navigate to the downloaded zip file and select it

5. Click "Install Add-on"

6. Find "Mesh: Instant Meshes Remeshing" in the addon list

7. Enable the addon by checking the box next to its name

8. Expand the addon preferences by clicking the arrow next to its name

9. Enter the full path to the Instant Meshes executable in the text field

10. Click the "Test Executable" button to verify that Blender can find and run the executable

## Usage

1. Open or create a 3D model in Blender

2. Select the object you want to remesh

3. Open the sidebar in the 3D View by pressing "N" or clicking the small arrow on the right side

4. Find the "Instant Meshes" tab in the sidebar

5. Configure the remeshing settings

6. Click "Apply Instant Meshes" to start the remeshing process

7. After processing, a new remeshed object will be created and selected

## Troubleshooting

### "Instant Meshes executable not found"
* Make sure you entered the correct full path to the executable
* Verify the executable has run permissions (`chmod +x`)
* Try running the executable directly from terminal to ensure it works

### "Process failed"
* Check if your mesh has non-manifold geometry
* Try with a simpler mesh first
* Increase the target count if the mesh is too complex

### AttributeError: Calling operator "bpy.ops.export_scene.obj" error
* This error occurs when the OBJ format addon is not enabled in Blender
* The addon will automatically fall back to using a built-in OBJ handler
* For best results, enable the "Import-Export: Wavefront OBJ format" addon in Blender:
  1. Go to Edit → Preferences → Add-ons
  2. Search for "obj"
  3. Enable the checkbox next to "Import-Export: Wavefront OBJ format"

## Compatibility

This addon has been tested with:
- Blender 4.4.0

## License

This addon is distributed under the terms of the Apache License, Version 2.0 (January 2004).

Instant Meshes is distributed under a modified 3-clause BSD license.