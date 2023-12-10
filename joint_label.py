"""Joint labler """
import json
import os
import cv2
import numpy as np
import argparse
import open3d as o3d


class JointLabler:
    """Labelling joint on images given joint information"""

    def __init__(self):
        self.joint_info = None
        self.cam_info = None
        self.poses_info = None
        self.pcd = None
        self.joint_dict = {}

    def read_info(self, info_file, cam_info_file, poses_info_file, ply_file=None):
        """Read joint information from file"""
        with open(info_file, 'r') as f:
            self.joint_info = json.load(f)
        self.parse_joint_info()
        with open(cam_info_file, 'r') as f:
            self.cam_info = json.load(f)
        with open(poses_info_file, 'r') as f:
            self.poses_info = json.load(f)
        with open(ply_file, 'r') as f:
            self.pcd = o3d.io.read_triangle_mesh(ply_file)

    def parse_joint_info(self):
        """Parse joint information"""
        self.joint_dict = {}
        for joint_data in self.joint_info:
            id = joint_data["id"]
            parent = joint_data["parent"]
            if joint_data["joint"] == "hinge":
                axis_origin = np.array(joint_data["jointData"]["axis"]["origin"])
                axis_direction = np.array(joint_data["jointData"]["axis"]["direction"])
                # Convert y-up to z-up
                axis_origin = np.array([-axis_origin[2], -axis_origin[0], axis_origin[1]])
                axis_direction = np.array([-axis_direction[2], -axis_direction[0], axis_direction[1]])
                self.joint_dict[id] = {
                    "id": id,
                    "parent": parent,
                    "type": "hinge",
                    "axis_origin": axis_origin,
                    "axis_direction": axis_direction
                }
            elif joint_data["joint"] == "slider":
                axis_origin = np.array(joint_data["jointData"]["axis"]["origin"])
                axis_direction = np.array(joint_data["jointData"]["axis"]["direction"])
                # Convert y-up to z-up
                axis_origin = np.array([-axis_origin[2], -axis_origin[0], axis_origin[1]])
                axis_direction = np.array([-axis_direction[2], -axis_direction[0], axis_direction[1]])
                self.joint_dict[id] = {
                    "id": id,
                    "parent": parent,
                    "type": "slider",
                    "axis_origin": axis_origin,
                    "axis_direction": axis_direction
                }

    def label_images(self, image_folder):
        """Label all images in the folder"""
        for image_file in sorted(os.listdir(image_folder), key=lambda x: int(x.split('.')[0])):
            # Read image
            image_file = os.path.join(image_folder, image_file)
            image_id = int(os.path.basename(image_file).split('.')[0])
            image = cv2.imread(image_file)
            # Read poses
            camera_pose = np.array(self.poses_info['cam_poses'][image_id]).reshape(4, 4)
            robot_pose = np.array(self.poses_info['robot_pose']).reshape(4, 4)
            # Read camera intrinsics
            cam_intrinsics = np.array([
                [self.cam_info['fx'], 0, self.cam_info['cx']],
                [0, self.cam_info['fy'], self.cam_info['cy']],
                [0, 0, 1]
            ])
            # Label image
            labeled_image = self.label_one_image(image, camera_pose, robot_pose, cam_intrinsics)
            # Show image
            cv2.imshow('image', image)
            cv2.waitKey(0)

    def label_one_image(self, image, camera_pose, robot_pose, cam_intrinsics) -> np.ndarray:
        """Label one image"""
        world2camera = np.linalg.inv(camera_pose)
        # world2camera = camera_pose
        # project all joints to image
        for joint_id, joint_data in self.joint_dict.items():
            if joint_data['type'] == 'hinge' or joint_data['type'] == 'slider':
                # Get joint origin & direction
                joint_origin = np.array(joint_data['axis_origin'])
                joint_direction = np.array(joint_data['axis_direction'])
                joint_pos_point = joint_origin + joint_direction * 1.0
                joint_neg_point = joint_origin - joint_direction * 1.0
                # Transform joint origin & direction to world frame
                joint_origin = np.dot(robot_pose, np.append(joint_origin, 1))[:3]
                joint_pos_point = np.dot(robot_pose, np.append(joint_pos_point, 1))[:3]
                joint_neg_point = np.dot(robot_pose, np.append(joint_neg_point, 1))[:3]
                # Transform joint origin & direction to camera frame
                joint_origin = np.dot(world2camera, np.append(joint_origin, 1))[:3]
                joint_pos_point = np.dot(world2camera, np.append(joint_pos_point, 1))[:3]
                joint_neg_point = np.dot(world2camera, np.append(joint_neg_point, 1))[:3]
                # Projection to image
                joint_origin_pixel = joint_origin[:2] / joint_origin[2]
                joint_origin_pixel[0] = -joint_origin_pixel[0] * self.cam_info['fx'] + self.cam_info['cx']
                joint_origin_pixel[1] = joint_origin_pixel[1] * self.cam_info['fy'] + self.cam_info['cy']
                joint_pos_point_pixel = joint_pos_point[:2] / joint_pos_point[2]
                joint_pos_point_pixel[0] = -joint_pos_point_pixel[0] * self.cam_info['fx'] + self.cam_info['cx']
                joint_pos_point_pixel[1] = joint_pos_point_pixel[1] * self.cam_info['fy'] + self.cam_info['cy']
                joint_neg_point_pixel = joint_neg_point[:2] / joint_neg_point[2]
                joint_neg_point_pixel[0] = -joint_neg_point_pixel[0] * self.cam_info['fx'] + self.cam_info['cx']
                joint_neg_point_pixel[1] = joint_neg_point_pixel[1] * self.cam_info['fy'] + self.cam_info['cy']

                # Draw joint line
                image = cv2.line(image, tuple(joint_pos_point_pixel.astype(np.int32)), tuple(joint_neg_point_pixel.astype(np.int32)), (0, 255, 0), 2)
                image = cv2.circle(image, tuple(joint_pos_point_pixel.astype(np.int32)), 5, (255, 0, 0), -1)
                image = cv2.circle(image, tuple(joint_neg_point_pixel.astype(np.int32)), 5, (0, 0, 255), -1)
                # Draw joint origin
                image = cv2.circle(image, tuple(joint_origin_pixel.astype(np.int32)), 5, (0, 255, 0), -1)
        return image

    def show_point_cloud(self):
        if self.pcd is not None:
            o3d.visualization.draw_geometries([self.pcd])


if __name__ == "__main__":
    # Parse arguments
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--data_name', type=str, default='102145')
    argparser.add_argument('--output_dir', type=str, default='output')
    args = argparser.parse_args()

    data_name = args.data_name
    data_folder = os.path.join(args.output_dir, 'coco_data', data_name)
    data_file = f'test_data/{data_name}/mobility.urdf'
    ply_file = os.path.join(data_folder, 'collision_obj.ply')
    info_file = os.path.join(data_folder, 'mobility_v2.json')
    poses_file = os.path.join(data_folder, 'poses_info.json')
    cam_info_file = os.path.join(data_folder, 'camera.json')

    # Init joint labeler
    joint_labeler = JointLabler()
    joint_labeler.read_info(info_file, cam_info_file, poses_file, ply_file)

    # Start labeling
    image_folder = os.path.join(data_folder, 'images')
    joint_labeler.label_images(image_folder)
    joint_labeler.show_point_cloud()
