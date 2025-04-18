# Copyright 2025 BlenderLab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

bl_info = {
    "name": "Instant Meshes Remeshing",
    "author": "BlenderLab",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Instant Meshes",
    "description": "Remesh objects using Instant Meshes",
    "warning": "",
    "doc_url": "",
    "category": "Mesh",
    "support": "TESTING",
    "wiki_url": "https://github.com/limbicnation/instant-meshes-blender-addon",
    "tracker_url": "https://github.com/limbicnation/instant-meshes-blender-addon/issues"
}

import bpy
import os
import subprocess
import tempfile
import bmesh
from pathlib import Path
import math
from bpy.props import (
    StringProperty,
    EnumProperty,
    IntProperty,
    BoolProperty,
    FloatProperty,
)
from bpy.types import (
    Operator,
    Panel,
    AddonPreferences,
)

class InstantMeshesAddonPreferences(AddonPreferences):
    bl_idname = __name__

    executable_path: StringProperty(
        name="Executable Path",
        description="Path to the Instant Meshes executable",
        default="",
        subtype='FILE_PATH',
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Instant Meshes Executable:")
        row = layout.row()
        row.prop(self, "executable_path", text="")
        row.operator("instantmeshes.test_executable", text="Test Executable")

class InstantMeshesTestExecutable(Operator):
    bl_idname = "instantmeshes.test_executable"
    bl_label = "Test Instant Meshes Executable"
    bl_description = "Test if the Instant Meshes executable can be found and run"

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        executable_path = prefs.executable_path

        if not executable_path:
            self.report({'ERROR'}, "No executable path set")
            return {'CANCELLED'}

        if not os.path.exists(executable_path):
            self.report({'ERROR'}, "Executable not found at specified path")
            return {'CANCELLED'}
            
        # Check if the file is executable
        if not os.access(executable_path, os.X_OK):
            self.report({'ERROR'}, 
                       f"File exists but is not executable. Run 'chmod +x \"{executable_path}\"' in terminal")
            return {'CANCELLED'}

        try:
            # Log the command being run
            print(f"Testing Instant Meshes executable: {executable_path}")
            
            # Run with --help to test basic functionality
            result = subprocess.run([executable_path, "--help"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   timeout=10,  # Increased timeout
                                   check=False)
            
            # Always log output regardless of result
            stdout = result.stdout.decode('utf-8', errors='replace')
            stderr = result.stderr.decode('utf-8', errors='replace')
            print(f"Instant Meshes test stdout: {stdout}")
            print(f"Instant Meshes test stderr: {stderr}")
            
            if result.returncode == 0:
                self.report({'INFO'}, "Instant Meshes executable is working correctly")
                return {'FINISHED'}
            else:
                # Create a more detailed error message
                error_msg = stderr.strip() if stderr.strip() else "No error output (check console for details)"
                
                # Check for common issues
                if "cannot open shared object file" in stderr:
                    self.report({'ERROR'}, 
                               f"Missing library dependencies: {error_msg}\n\n"
                               f"Try running: sudo apt install libgl1-mesa-glx libglu1-mesa zenity libxrandr-dev "
                               f"libxinerama-dev libxcursor-dev libxi-dev")
                elif "Permission denied" in stderr:
                    self.report({'ERROR'}, 
                               f"Permission denied. Make sure the file is executable: chmod +x \"{executable_path}\"")
                else:
                    self.report({'ERROR'}, f"Executable test failed: {error_msg}")
                
                return {'CANCELLED'}
                
        except subprocess.TimeoutExpired:
            self.report({'ERROR'}, 
                       "Executable test timed out. The program may be hanging or waiting for input. "
                       "Try running it directly from the terminal to debug.")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error testing executable: {str(e)}")
            print(f"Detailed error: {type(e).__name__}: {str(e)}")
            return {'CANCELLED'}

def write_obj_file(obj, filepath, triangulate=True):
    """
    Manually write an OBJ file for the given object
    
    Args:
        obj: The Blender object to export
        filepath: The path to write the OBJ file to
        triangulate: Whether to triangulate the mesh
    """
    mesh = obj.data
    matrix = obj.matrix_world
    
    # Create a bmesh from the mesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    # Triangulate if requested
    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)
    
    # Open the file for writing
    with open(filepath, 'w') as f:
        # Write header
        f.write("# OBJ file created by Instant Meshes Blender Addon\n")
        
        # Write vertices
        for v in bm.verts:
            # Transform vertex by object matrix
            co = matrix @ v.co
            f.write(f"v {co.x:.6f} {co.y:.6f} {co.z:.6f}\n")
        
        # Write normals
        for v in bm.verts:
            # Transform normal by object matrix (without translation)
            normal = matrix.to_3x3() @ v.normal
            normal.normalize()
            f.write(f"vn {normal.x:.6f} {normal.y:.6f} {normal.z:.6f}\n")
        
        # Write faces
        for face in bm.faces:
            # Collect vertex indices (OBJ uses 1-based indexing)
            indices = [str(v.index + 1) for v in face.verts]
            
            # Add vertex normal indices
            indices_with_normals = [f"{idx}//{idx}" for idx in indices]
            
            # Write face
            f.write(f"f {' '.join(indices_with_normals)}\n")
    
    # Free the bmesh
    bm.free()


def read_obj_file(filepath, context):
    """
    Import an OBJ file and return the created object
    
    Args:
        filepath: The path to the OBJ file
        context: The Blender context
        
    Returns:
        The imported Blender object, or None if import failed
    """
    try:
        # First try to use the built-in OBJ importer if available
        if hasattr(bpy.ops.import_scene, "obj"):
            bpy.ops.import_scene.obj(filepath=filepath, global_scale=1.0)
            if len(context.selected_objects) > 0:
                return context.selected_objects[0]
        
        # If that fails, parse the OBJ file manually
        mesh = bpy.data.meshes.new("ImportedMesh")
        obj = bpy.data.objects.new("ImportedObject", mesh)
        
        vertices = []
        faces = []
        
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    # Parse vertex
                    parts = line.split()
                    if len(parts) >= 4:
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        vertices.append((x, y, z))
                elif line.startswith('f '):
                    # Parse face
                    parts = line.split()
                    face_verts = []
                    for p in parts[1:]:
                        # Handle vertex/texture/normal format
                        vert_index = p.split('/')[0]
                        # OBJ uses 1-based indexing, so subtract 1
                        face_verts.append(int(vert_index) - 1)
                    faces.append(face_verts)
        
        # Create the mesh
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        
        # Link the object to the scene
        context.collection.objects.link(obj)
        
        # Select and make active
        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        
        return obj
    
    except Exception as e:
        print(f"Error importing OBJ file: {str(e)}")
        return None


class InstantMeshesRemeshOperator(Operator):
    bl_idname = "instantmeshes.remesh"
    bl_label = "Apply Instant Meshes"
    bl_description = "Remesh the selected object using Instant Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        executable_path = prefs.executable_path
        
        if not executable_path or not os.path.exists(executable_path):
            self.report({'ERROR'}, "Instant Meshes executable not found")
            return {'CANCELLED'}
            
        obj = context.active_object
        scene = context.scene
        props = scene.instant_meshes_properties
        
        # Create temporary directory for input/output files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export the selected object to OBJ
            input_path = os.path.join(temp_dir, "input.obj")
            output_path = os.path.join(temp_dir, "output.obj")
            
            # Remember original object data and transformation
            original_data = obj.data
            original_matrix = obj.matrix_world.copy()
            
            # Export to OBJ using our custom function instead of the OBJ exporter
            write_obj_file(obj, input_path, triangulate=True)
            
            # Build Instant Meshes command
            cmd = [executable_path, "-i", input_path, "-o", output_path]
            
            # Target count type
            if props.target_count_type == 'FACES':
                cmd.extend(["-f", str(props.face_count)])
            else:
                cmd.extend(["-v", str(props.vertex_count)])
                
            # Other options
            if props.preserve_sharp:
                cmd.append("-c")
            
            if props.align_to_boundaries:
                cmd.append("-b")
                
            if props.deterministic:
                cmd.append("-d")
                
            if props.crease_angle > 0:
                cmd.extend(["-a", str(props.crease_angle)])
            
            # Run Instant Meshes
            try:
                self.report({'INFO'}, "Running Instant Meshes, please wait...")
                
                # Log the command being run for debugging
                print(f"Running command: {' '.join(cmd)}")
                
                # Use a more robust process handling approach
                process = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=120  # 2-minute timeout to prevent hanging
                )
                
                # For debugging, always log output
                stdout = process.stdout.decode('utf-8', errors='replace')
                stderr = process.stderr.decode('utf-8', errors='replace')
                print(f"Instant Meshes stdout: {stdout}")
                print(f"Instant Meshes stderr: {stderr}")
                
                if process.returncode != 0:
                    # Create a user-friendly error message
                    error_msg = stderr.strip()
                    if not error_msg:
                        error_msg = "Unknown error (no error message returned)"
                        # Try to get more information about the executable
                        try:
                            file_info = subprocess.run(
                                ["file", executable_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                timeout=5,
                                check=False
                            ).stdout.decode('utf-8', errors='replace')
                            
                            # Check file type for common issues
                            print(f"File info: {file_info}")
                            
                            if "shell script" in file_info.lower():
                                error_msg = (
                                    "The executable appears to be a shell script. "
                                    "Make sure it has executable permissions: chmod +x \"" + executable_path + "\""
                                )
                            elif "elf" in file_info.lower():
                                if "32-bit" in file_info and "64-bit" not in file_info:
                                    error_msg = (
                                        "The executable is a 32-bit binary but you're likely on a 64-bit system. "
                                        "You need to install 32-bit compatibility libraries: "
                                        "sudo apt install lib32stdc++6 lib32z1"
                                    )
                                elif "64-bit" in file_info:
                                    error_msg = (
                                        "The executable is a 64-bit binary but failed silently. "
                                        "This usually indicates missing dependencies. Try: "
                                        "sudo apt install libgl1-mesa-glx libglu1-mesa zenity libxrandr-dev "
                                        "libxinerama-dev libxcursor-dev libxi-dev"
                                    )
                            elif "text" in file_info.lower():
                                error_msg = (
                                    "The file appears to be a text file, not an executable. "
                                    "Make sure you have the correct path to the Instant Meshes binary."
                                )
                        except Exception as e:
                            print(f"Failed to get file info: {str(e)}")
                    
                    # Look for common errors and provide solutions
                    if "cannot open shared object file" in error_msg:
                        error_msg += (
                            "\n\nThis appears to be a missing library dependency. "
                            "Try installing: sudo apt install libgl1-mesa-glx libglu1-mesa zenity libxrandr-dev "
                            "libxinerama-dev libxcursor-dev libxi-dev"
                        )
                    elif "No such file or directory" in error_msg:
                        error_msg += (
                            "\n\nThe Instant Meshes executable could not be run. "
                            "Make sure it has executable permissions: chmod +x 'path/to/Instant Meshes'"
                        )
                    elif "Permission denied" in error_msg:
                        error_msg += (
                            "\n\nThe Instant Meshes executable doesn't have execute permissions. "
                            f"Run: chmod +x \"{executable_path}\""
                        )
                    
                    # Report error
                    self.report({'ERROR'}, f"Instant Meshes failed: {error_msg}")
                    return {'CANCELLED'}
                    
                if not os.path.exists(output_path):
                    # Check for specific reasons why the output might not be created
                    if "Cannot initialize NanoGUI" in stdout or "Cannot initialize NanoGUI" in stderr:
                        self.report({'ERROR'}, 
                                   "Instant Meshes GUI initialization failed. This typically happens when "
                                   "running headless or with missing X11 dependencies. Try installing: "
                                   "sudo apt install libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev zenity")
                    elif "failed to reproject" in stdout or "failed to reproject" in stderr:
                        self.report({'ERROR'}, 
                                   "Instant Meshes failed to reproject the mesh. Try with a simpler mesh "
                                   "or increase the target face/vertex count.")
                    else:
                        self.report({'ERROR'}, 
                                   "Output file not created. Instant Meshes may have encountered an internal error "
                                   "processing your mesh. Try with a different mesh or check the console for details.")
                    return {'CANCELLED'}
                    
                # Import the result using our custom function
                new_obj = read_obj_file(output_path, context)
                
                # Check if import was successful
                if new_obj:
                    # Apply original transformation
                    new_obj.matrix_world = original_matrix
                    
                    # Rename object
                    new_obj.name = f"{obj.name}_remeshed"
                    
                    # Set as active object
                    context.view_layer.objects.active = new_obj
                    
                    self.report({'INFO'}, "Remeshing completed successfully")
                    return {'FINISHED'}
                else:
                    self.report({'ERROR'}, "Failed to import remeshed model")
                    return {'CANCELLED'}
                    
            except Exception as e:
                self.report({'ERROR'}, f"Error during remeshing: {str(e)}")
                return {'CANCELLED'}

class InstantMeshesProperties(bpy.types.PropertyGroup):
    target_count_type: EnumProperty(
        name="Target Count",
        description="Choose between target face count or vertex count",
        items=[
            ('FACES', "Faces", "Target face count"),
            ('VERTICES', "Vertices", "Target vertex count"),
        ],
        default='FACES'
    )
    
    face_count: IntProperty(
        name="Face Count",
        description="Target number of faces",
        default=5000,
        min=10,
        max=1000000
    )
    
    vertex_count: IntProperty(
        name="Vertex Count",
        description="Target number of vertices",
        default=5000,
        min=10,
        max=1000000
    )
    
    preserve_sharp: BoolProperty(
        name="Preserve Sharp Edges",
        description="Preserve sharp features and corners",
        default=True
    )
    
    align_to_boundaries: BoolProperty(
        name="Align to Boundaries",
        description="Align to mesh boundaries",
        default=True
    )
    
    deterministic: BoolProperty(
        name="Deterministic",
        description="Deterministic mode (slower but more stable)",
        default=False
    )
    
    crease_angle: FloatProperty(
        name="Crease Angle",
        description="Dihedral angle threshold for creases (degrees)",
        default=30.0,
        min=0.0,
        max=180.0
    )

class InstantMeshesPanel(Panel):
    bl_label = "Instant Meshes"
    bl_idname = "VIEW3D_PT_instant_meshes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Instant Meshes"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.instant_meshes_properties
        
        # Check if executable path is set
        prefs = context.preferences.addons[__name__].preferences
        if not prefs.executable_path or not os.path.exists(prefs.executable_path):
            layout.label(text="Executable not set or invalid", icon='ERROR')
            layout.operator("preferences.addon_show", text="Open Preferences").module=__name__
            return
            
        # Main panel
        box = layout.box()
        row = box.row()
        row.prop(props, "target_count_type", expand=True)
        
        if props.target_count_type == 'FACES':
            box.prop(props, "face_count")
        else:
            box.prop(props, "vertex_count")
            
        box.prop(props, "preserve_sharp")
        box.prop(props, "align_to_boundaries")
        box.prop(props, "deterministic")
        box.prop(props, "crease_angle")
        
        # Add a button to apply the remeshing
        layout.operator("instantmeshes.remesh")

classes = (
    InstantMeshesAddonPreferences,
    InstantMeshesTestExecutable,
    InstantMeshesRemeshOperator,
    InstantMeshesProperties,
    InstantMeshesPanel,
)

def check_dependencies():
    """Check if required dependencies are available and log warnings if not."""
    # Let users know if the OBJ import/export is not available
    obj_import_available = hasattr(bpy.ops.import_scene, "obj")
    obj_export_available = hasattr(bpy.ops.export_scene, "obj")
    
    if not obj_import_available or not obj_export_available:
        print("WARNING: OBJ import/export addons are not enabled. The Instant Meshes addon will use a built-in OBJ handler instead.")
        print("For best results, enable the 'Import-Export: Wavefront OBJ format' addon in Blender preferences.")
    
    # Check for system utilities that we use
    system_tools = ['file', 'chmod']
    missing_tools = []
    
    for tool in system_tools:
        try:
            # Try to run the tool with a simple command
            subprocess.run(
                [tool, "--version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                timeout=2,
                check=False
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"WARNING: Missing system utilities: {', '.join(missing_tools)}")
        print("Some error detection features may not work correctly.")
    
    return True

def register():
    # Check for dependencies
    check_dependencies()
    
    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register properties
    bpy.types.Scene.instant_meshes_properties = bpy.props.PointerProperty(type=InstantMeshesProperties)

def unregister():
    # Unregister properties
    del bpy.types.Scene.instant_meshes_properties
    
    # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()