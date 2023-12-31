import blenderproc as bproc
import bpy
import os
import argparse
import json
import numpy as np
from blenderproc.python.writer.BopWriterUtility import _BopWriterUtility

# import debugpy
# debugpy.listen(5678)
# debugpy.wait_for_client()
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

# -------------------------- Main -------------------------- #
argparser = argparse.ArgumentParser()
argparser.add_argument("--data_name", type=str, default="100162")
argparser.add_argument("--output_dir", type=str, default="output")
argparser.add_argument("--num_poses", type=int, default=10)
argparser.add_argument("--light_radius_min", type=float, default=3.0)
argparser.add_argument("--light_radius_max", type=float, default=5.0)
argparser.add_argument("--cam_radius_min", type=float, default=3.0)
argparser.add_argument("--cam_radius_max", type=float, default=5.0)
argparser.add_argument("--img_width", type=int, default=640)
argparser.add_argument("--img_height", type=int, default=480)
argparser.add_argument("--disable_top_sampling", action="store_true")
args = argparser.parse_args()

# Set parameters
output_dir = args.output_dir
data_name = args.data_name
data_file = f"test_data/{data_name}/mobility.urdf"
num_poses = args.num_poses
light_radius_min = args.light_radius_min
light_radius_max = args.light_radius_max
cam_radius_min = args.cam_radius_min
cam_radius_max = args.cam_radius_max

robot_pose = [np.eye(4).tolist()]
cam_poses = []

# -------------------------- Init & Load -------------------------- #
bproc.init()

# Load URDF mesh into scene
robot = bproc.loader.load_urdf(data_file)
# Randomly rotatet the robot
revolute_joints = robot.get_links_with_revolute_joints()
num_revolute_joints = len(revolute_joints)
# random_rotations = np.random.uniform(0.0, 1.0, num_revolute_joints).tolist()  # FIXME: how to set a better range?
# robot.set_rotation_euler_fk(link=None, rotation_euler=random_rotations)

# -------------------------- Semantic -------------------------- #
mesh_objs = []
link_rep_objs = []  # link representation objects
for idx_link, link in enumerate(robot.links):
    link_objs = []  # all objects in this link
    for visual in link.visuals:
        visual.set_cp("category_id", idx_link)
        link_objs.append(visual)
    mesh_objs += link_objs
    if link_objs:
        link_rep_objs.append(link_objs[0])

# -------------------------- Light -------------------------- #
# Background light
light_background = bproc.types.Light(light_type="SUN")
light_background.set_energy(5)
light_background.set_color(np.random.uniform([0.5, 0.5, 0.5], [1, 1, 1]))
light_background.set_location([np.random.random(), np.random.random(), 10])

# Point light
light_point = bproc.types.Light(light_type="POINT")
light_point.set_energy(200)
light_point.set_color(np.random.uniform([0.5, 0.5, 0.5], [1, 1, 1]))
location = bproc.sampler.shell(
    center=[0, 0, 0],
    radius_min=light_radius_min,
    radius_max=light_radius_max,
    elevation_min=5,
    elevation_max=89,
    uniform_volume=False,
)
light_point.set_location(location)

# -------------------------- Camera -------------------------- #
# Set camera resolution
bproc.camera.set_resolution(args.img_width, args.img_height)

# BVH tree used for camera obstacle checks
bop_bvh_tree = bproc.object.create_bvh_tree_multi_objects(mesh_objs)

poses = 0
# Render two camera poses
while poses < num_poses:
    # Sample location
    location = bproc.sampler.shell(
        center=[0, 0, 0],
        radius_min=cam_radius_min,
        radius_max=cam_radius_max,
        elevation_min=1,
        elevation_max=89,
        uniform_volume=False,
    )
    # Check if location too close to robot
    if (np.abs(location[0]) < 0.3 * cam_radius_min) and (np.abs(location[1]) < 0.3 * cam_radius_min):
        continue

    # Determine point of interest in scene as the object closest to the mean of a subset of objects
    poi = bproc.object.compute_poi(mesh_objs)
    # Compute rotation based on vector going from location towards poi
    # rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location,
    #                                                          inplane_rot=np.random.uniform(-0.7854, 0.7854))
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=0.0)
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)

    # Check that obstacles are at least 0.3 meter away from the camera and make sure the view interesting enough
    if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 0.3}, bop_bvh_tree):
        # Persist camera pose
        bproc.camera.add_camera_pose(cam2world_matrix, frame=poses)
        poses += 1
        cam_poses.append(cam2world_matrix.tolist())

# -------------------------- Render & Save -------------------------- #
bproc.renderer.enable_depth_output(activate_antialiasing=False)
# enable segmentation masks (per class and per instance)
bproc.renderer.enable_segmentation_output(map_by=["category_id", "instance"])

# Render the segmentation under Cycles engine
bpy.context.scene.render.engine = "CYCLES"
data = bproc.renderer.render(load_keys={"segmap"})
# Render color and depth under Eevee engine
bpy.context.scene.render.engine = "BLENDER_EEVEE"
data.update(bproc.renderer.render(load_keys={"colors", "depth"}))

# # Write the rendering into an hdf5 file
# bproc.writer.write_hdf5(output_dir, data)

# Write data to coco file
joint_file = f"test_data/{data_name}/mobility_v2.json"
with open(joint_file, "r") as f:
    joint_info = json.load(f)

# build a new instance_attribute_maps
instance_attribute_maps = []
for i in range(len(data["instance_segmaps"])):
    instance_attribute_maps.append([])
    for j in range(len(robot.links)):
        # Use first part name as the link name
        link_name = robot.links[j].blender_obj.name
        if link_name == "base":
            link_name = "base_link"
        else:
            link_id = int(link_name.split("_")[1])
            link_name = joint_info[link_id]["parts"][0]["name"]
        instance_attribute_maps[i].append(
            {
                "category_id": j,
                "idx": j,
                # "name": f"link_{j}"
                "name": link_name,
            }
        )

bproc.writer.write_coco_annotations(
    os.path.join(output_dir, "coco_data", data_name),
    instance_segmaps=data["category_id_segmaps"],
    instance_attribute_maps=instance_attribute_maps,
    colors=data["colors"],
    color_file_format="JPEG",
)

# Load previous poses_info if exists
poses_info = {}
if os.path.exists(os.path.join(output_dir, "coco_data", data_name, "poses_info.json")):
    with open(os.path.join(output_dir, "coco_data", data_name, "poses_info.json"), "r") as f:
        poses_info = json.load(f)
else:
    poses_info["cam_poses"] = []
    poses_info["robot_pose"] = []

# Add new poses
poses_info["cam_poses"] += cam_poses
poses_info["robot_pose"] += robot_pose

# Write camera info
_BopWriterUtility.write_camera(os.path.join(output_dir, "coco_data", data_name, "camera.json"))
with open(os.path.join(output_dir, "coco_data", data_name, "poses_info.json"), "w") as f:
    json.dump(poses_info, f)

# Copy joint file
os.system(f'cp {joint_file} {os.path.join(output_dir, "coco_data", data_name)}')

# Export ply file
all_mesh_objs = robot.get_all_collision_objs()
# all_mesh_objs = robot.get_all_visual_objs()
# join all meshes
merged_mesh_objs = all_mesh_objs[1]
# merged_mesh_objs.join_with_other_objects(all_mesh_objs[1:])
# export to ply

bpy.context.view_layer.objects.active = merged_mesh_objs.blender_obj
export_ply_file = os.path.join(output_dir, "coco_data", data_name, "collision_obj.ply")
# Export the selected object
bpy.ops.export_mesh.ply(filepath=export_ply_file)
