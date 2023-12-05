import blenderproc as bproc
import bpy
import os
import trimesh
import numpy as np
import yourdfpy
import re
import debugpy

# -------------------------- Utils Functions -------------------------- #


def locate_joint_children(urdf, joint_type="revolute"):
    """Locate the child link for all revolute joints in urdf"""
    for joint in urdf.robot.joints:
        if joint.type == joint_type:
            yield joint.child
        elif joint.type == "fixed":
            yield joint.child
        elif joint.type == "prismatic":
            yield joint.child


def build_link_to_visual_map(urdf):
    """Build a map from link name to visual mesh"""
    link_to_visual = {}
    for link in urdf.robot.links:
        if link.name not in link_to_visual:
            link_to_visual[link.name] = []
        for visual in link.visuals:
            link_to_visual[link.name].append(visual.name)
    return link_to_visual


def remove_numeric_postfix(s):
    return re.sub(r"_\d+$", "", s)


# -------------------------- Main -------------------------- #
# # debug
debugpy.listen(5678)
debugpy.wait_for_client()


bproc.init()

# Load the URDF file
output_dir = 'output'
data_name = '47645'
data_file = f'test_data/{data_name}/mobility.urdf'
urdf = yourdfpy.URDF.load(data_file)

# Compute joint part
revolute_child_links = list(locate_joint_children(urdf, joint_type="revolute"))
prismatic_child_links = list(locate_joint_children(urdf, joint_type="prismatic"))
link_to_visual = build_link_to_visual_map(urdf)
visual_to_link = {v: k for k, v_list in link_to_visual.items() for v in v_list}

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
        bsdf.location = (0, 0)

        # Create a Material Output node and link to bsdf
        material_output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
        material_output.location = (200, 0)
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

# Sample light
light_point = bproc.types.Light()
light_point.set_energy(200)
light_point.set_color(np.random.uniform([0.5, 0.5, 0.5], [1, 1, 1]))
location = bproc.sampler.shell(center=[0, 0, 0], radius_min=1, radius_max=1.5,
                               elevation_min=5, elevation_max=89, uniform_volume=False)
light_point.set_location(location)

# Set shade smooth
# Iterate over all objects in the scene
objs_focus = []
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

        # Set object's link attribute
        obj_name = remove_numeric_postfix(obj.name)
        # obj.set_cp("category_id", visual_to_link[obj_name])
        link_name = visual_to_link[obj_name]
        obj["category_id"] = 0 if link_name == "base" else int(link_name.split("_")[-1]) + 1
        objs_focus.append(obj)

# Sample camera pose
poses = 0
while poses < 10:
    # Sample location
    location = bproc.sampler.shell(center=[0, 0, 0],
                                   radius_min=5.0,
                                   radius_max=10.0,
                                   elevation_min=5,
                                   elevation_max=89,
                                   uniform_volume=False)
    # Determine point of interest in scene as the object closest to the mean of a subset of objects
    poi = bproc.object.compute_poi(np.random.choice(objs_focus, size=10))
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)

    # Persist camera pose
    bproc.camera.add_camera_pose(cam2world_matrix)
    poses += 1

# activate depth rendering
bproc.renderer.enable_depth_output(activate_antialiasing=False)
# enable segmentation masks (per class and per instance)
bproc.renderer.enable_segmentation_output(map_by=["category_id", "instance", "name"])

# Render the scene
data = bproc.renderer.render()

# Write the rendering into an hdf5 file
bproc.writer.write_hdf5(output_dir, data)
