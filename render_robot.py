import blenderproc as bproc
import bpy
import os
import trimesh
import numpy as np
import yourdfpy

# debug
# import debugpy
# debugpy.listen(5678)
# debugpy.wait_for_client()

bproc.init()

# Load the URDF file
data_file =  'test_data/102145/mobility.urdf'
urdf = yourdfpy.URDF.load(data_file)

for name, trimesh_mesh in urdf.scene.geometry.items():
    # Create a simple object:
    blender_mesh = bpy.data.meshes.new(name=name)
    blender_obj = bpy.data.objects.new(name, blender_mesh)

    # Link the object to the scene
    bpy.context.collection.objects.link(blender_obj)

    # Get the vertices and faces from trimesh
    vertices = [tuple(vertex) for vertex in trimesh_mesh.vertices]
    faces = [tuple(face) for face in trimesh_mesh.faces]

    # Add the vertices and faces to the Blender mesh
    blender_mesh.from_pydata(vertices, [], faces)

    # Check if the mesh has a SimpleMaterial
    if isinstance(trimesh_mesh.visual.material, trimesh.visual.material.SimpleMaterial):
        # Create a new material
        material = bpy.data.materials.new(name=trimesh_mesh.visual.material.name)
        blender_obj.data.materials.append(material)

        # Enable 'Use Nodes' for the material
        material.use_nodes = True

        # Clear default nodes
        material.node_tree.nodes.clear()

        # Create a Principled BSDF shader node
        bsdf = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (0,0)

        # Create a Material Output node and link to bsdf
        material_output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
        material_output.location = (200,0)
        material.node_tree.links.new(bsdf.outputs['BSDF'], material_output.inputs['Surface'])

        # Extract ambient, diffuse, and specular properties
        ambient = trimesh_mesh.visual.material.ambient / 255.0
        diffuse = trimesh_mesh.visual.material.diffuse / 255.0
        specular = trimesh_mesh.visual.material.specular / 255.0

        # Set material properties in Blender
        bsdf.inputs['Base Color'].default_value = diffuse[:4]  # RGBA
        bsdf.inputs['Specular'].default_value = specular[0]  # Assuming monochromatic specular value
        bsdf.inputs['Roughness'].default_value = 1.0 - specular[1]  # Assuming glossiness value
        bsdf.inputs['Metallic'].default_value = 0.0  # No metallic effect
        # bsdf.inputs['Emission'].default_value = ambient[:3]  # RGB

    # Update mesh with new data
    blender_mesh.update()

# Create a point light next to it
light = bproc.types.Light()
light.set_location([2, -2, 0])
light.set_energy(300)

# Set shade smooth
# Iterate over all objects in the scene
for obj in bpy.data.objects:
    # Check if the object is a mesh
    if obj.type == 'MESH':
        # # Set the shading to smooth
        # bpy.context.view_layer.objects.active = obj
        # # Ensure we're in Object Mode for the active object
        # if obj.mode != 'OBJECT':
        #     bpy.ops.object.mode_set(mode='OBJECT')
        # bpy.ops.object.shade_smooth()
        with bpy.context.temp_override(selected_editable_objects=[obj]):
            bpy.ops.object.shade_smooth()

# Set the camera to be in front of the object
cam_pose = bproc.math.build_transformation_mat([0, 5, 0], [-np.pi / 2, 0, 0])
bproc.camera.add_camera_pose(cam_pose)

# Render the scene
data = bproc.renderer.render()

# Write the rendering into an hdf5 file
bproc.writer.write_hdf5("output/", data)