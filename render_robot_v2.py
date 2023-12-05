import blenderproc as bproc
import bpy
import os
import trimesh
import numpy as np
import re
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()


# -------------------------- Utils Functions -------------------------- #


# -------------------------- Main -------------------------- #

bproc.init()
# Load the URDF file
output_dir = 'output'
data_name = '47645'
data_file = f'test_data/{data_name}/mobility.urdf'
num_poses = 10
cam_radius_min = 3.0
cam_radius_max = 5.0
rot_scale = 0.3

# Load URDF mesh into scene
robot = bproc.loader.load_urdf(data_file)
# Randomly rotatet the robot
revolute_joints = robot.get_links_with_revolute_joints()
num_revolute_joints = len(revolute_joints)
random_rotations = np.random.uniform(0.0, 1.0, num_revolute_joints).tolist()  # FIXME: how to set a better range?
robot.set_rotation_euler_fk(link=None, rotation_euler=random_rotations)

# -------------------------- Semantic -------------------------- #
geometries = []
for idx_link, link in enumerate(robot.links):
    for visual in link.visuals:
        visual.set_cp("category_id", idx_link + 1)
        geometries.append(visual)

# -------------------------- Light -------------------------- #
light_point = bproc.types.Light()
light_point.set_energy(200)
light_point.set_color(np.random.uniform([0.5, 0.5, 0.5], [1, 1, 1]))
location = bproc.sampler.shell(center=[0, 0, 0], radius_min=1, radius_max=1.5,
                               elevation_min=5, elevation_max=89, uniform_volume=False)
light_point.set_location(location)

# -------------------------- Camera -------------------------- #
# BVH tree used for camera obstacle checks
bop_bvh_tree = bproc.object.create_bvh_tree_multi_objects(geometries)

poses = 0
# Render two camera poses
while poses < num_poses:
    # Sample location
    location = bproc.sampler.shell(center=[0, 0, 0],
                                   radius_min=cam_radius_min,
                                   radius_max=cam_radius_max,
                                   elevation_min=1,
                                   elevation_max=89,
                                   uniform_volume=False)
    # Determine point of interest in scene as the object closest to the mean of a subset of objects
    poi = bproc.object.compute_poi(geometries)
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location,
                                                             inplane_rot=np.random.uniform(-0.7854, 0.7854))
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)

    # Check that obstacles are at least 0.3 meter away from the camera and make sure the view interesting enough
    if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 0.3}, bop_bvh_tree):
        # Persist camera pose
        bproc.camera.add_camera_pose(cam2world_matrix,
                                     frame=poses)
        poses += 1

# -------------------------- Render & Save -------------------------- #
bproc.renderer.enable_depth_output(activate_antialiasing=False)
# enable segmentation masks (per class and per instance)
bproc.renderer.enable_segmentation_output(map_by=["category_id", "instance", "name"])

# Render the scene
data = bproc.renderer.render()

# Write the rendering into an hdf5 file
bproc.writer.write_hdf5(output_dir, data)

# Write data to coco file
# build a new instance_attribute_maps
instance_attribute_maps = []
for i in range(len(data["instance_segmaps"])):
    instance_attribute_maps.append([])
    for j in range(len(robot.links) + 1):
        instance_attribute_maps[i].append(
            {
                "category_id": j,
                "idx": j,
                "name": f"link_{j}"
            }
        )

bproc.writer.write_coco_annotations(os.path.join(output_dir, 'coco_data'),
                                    instance_segmaps=data["category_id_segmaps"],
                                    instance_attribute_maps=instance_attribute_maps,
                                    colors=data["colors"],
                                    color_file_format="JPEG")
