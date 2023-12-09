import blenderproc as bproc
import bpy
import os
import numpy as np

# -------------------------- Main -------------------------- #
# Load the obj file
output_dir = 'output'
data_name = '100162'
test_obj_file = os.path.join('test_data', data_name, 'textured_objs', 'original-1.obj')

bproc.init()
# obj = bproc.loader.load_obj(test_obj_file, use_legacy_obj_import=True)
bpy.ops.wm.obj_import(filepath=test_obj_file)
# bpy.ops.import_scene.obj(filepath=test_obj_file)
# Override engine
bpy.context.scene.render.engine = 'EEVEE'


# -------------------------- Light -------------------------- #
# light_point = bproc.types.Light()
# light_point.set_energy(200)
# light_point.set_color(np.random.uniform([0.5, 0.5, 0.5], [1, 1, 1]))
# location = bproc.sampler.shell(center=[0, 0, 0], radius_min=1, radius_max=1.5,
#                                elevation_min=5, elevation_max=89, uniform_volume=False)
# light_point.set_location(location)

# # Set camera
# cam_radius_min = 3.0
# cam_radius_max = 5.0
# location = bproc.sampler.shell(center=[0, 0, 0],
#                                radius_min=cam_radius_min,
#                                radius_max=cam_radius_max,
#                                elevation_min=1,
#                                elevation_max=89,
#                                uniform_volume=False)
# poi = np.array(0, 0, 0)
# rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location,
#                                                          inplane_rot=0.0)
# # Add homog cam pose based on location an rotation
# cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
# bproc.camera.add_camera_pose(cam2world_matrix, frame=0)

# # Render the scene
# data = bproc.renderer.render()

# # Save the data
# bproc.writer.write_hdf5(output_dir, data)
