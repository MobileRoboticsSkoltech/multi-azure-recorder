#!/usr/bin/env python3

import argparse
import json
import os
from shutil import rmtree
from tqdm import tqdm
import cv2
import numpy as np

class depth2rgb:

    def __init__(self, path_to_depth_params,
                path_to_rgb_params,
                path_to_extrinsics_params,
                path_to_rgb_camera_images,
                path_to_depth_camera_images,
                output_folder,
                rgb_format,
                depth_format):
        self.path_to_rgb_camera_images = path_to_rgb_camera_images
        self.path_to_depth_camera_images = path_to_depth_camera_images
        self.output_folder = output_folder
        self.rgb_format = rgb_format
        self.depth_format = depth_format

        ########### load dictionaries with intrinsics and extinsics ###########
        with open(path_to_depth_params) as f:
            temp = json.load(f)['depth_camera']
            par_d = temp['intrinsics']['parameters']["parameters_as_dict"]
            self.shape_d = (temp['resolution_height'], temp['resolution_width'])

        with open(path_to_rgb_params) as f:
            temp = json.load(f)['color_camera']
            par_c = temp['intrinsics']['parameters']["parameters_as_dict"]
            self.shape_c = (temp['resolution_height'], temp['resolution_width'])

        if (path_to_depth_params == path_to_rgb_params):
            with open(path_to_extrinsics_params) as f:
                extrinsics_params = json.load(f)["color_camera"]["extrinsics"]
        else:
            with open(path_to_extrinsics_params) as f:
                extrinsics_params = json.load(f)['CalibrationInformation']['Cameras'][1]['Rt']

        ########### Depth camera parameters ###########
        #D - vector of distortion coefficients, K - calibration matrix
        #d - index for depth
        Dd = [par_d['k1'], par_d['k2'], par_d['p1'], par_d['p2'],
              par_d['k3'], par_d['k4'], par_d['k5'], par_d['k6']]

        Kd = [par_d['fx'], 0.0        , par_d['cx'],
              0.0        , par_d['fy'], par_d['cy'],
              0.0        , 0.0        , 1.0]

        self.Dd = np.array(Dd)
        self.Kd = np.array(Kd).reshape((3, 3), order='C')

        ########### RGB camera parameters ###########
        #c - index for color
        Dc = [par_c['k1'], par_c['k2'], par_c['p1'], par_c['p2'],
              par_c['k3'], par_c['k4'], par_c['k5'], par_c['k6']]

        Kc = [par_c['fx'], 0.0        , par_c['cx'],
              0.0        , par_c['fy'], par_c['cy'],
              0.0        , 0.0        , 1.0]

        self.Dc = np.array(Dc)
        self.Kc = np.array(Kc).reshape((3, 3), order='C')

        ########### Extrinsics between cameras ###########
        if (path_to_depth_params == path_to_rgb_params):
            #Rotation
            R_ = np.array(extrinsics_params['rotation']).reshape((3, 3), order='C')
            #Translation
            T_ = np.array(extrinsics_params['translation_in_meters'])
        else:
            #Rotation
            R_ = np.array(extrinsics_params['Rotation']).reshape((3, 3), order='C')
            #Translation
            T_ = np.array(extrinsics_params['Translation'])

        self.T = np.hstack((R_, T_[:, None]))
        self.T = np.vstack((self.T, np.array([[0, 0, 0, 1]])))

        self.Kc_undistorted = self.undistort_calibration_matrix(self.shape_c, self.Kc, self.Dc)
        self.Kd_undistorted = self.undistort_calibration_matrix(self.shape_d, self.Kd, self.Dd)

    @staticmethod
    def undistort_calibration_matrix(shape, calibration_matrix, dist_coeff):
        """
        Returns undistorted calibration matrix.
        :param shape: shape of image [x, y]
        :param calibration_matrix: calibration matrix [3 x 3]
        :param dist_coeff: distortions' vector
        """
        undist_calibration, _ = cv2.getOptimalNewCameraMatrix(calibration_matrix, dist_coeff, shape, 1, shape)
        return undist_calibration

    @staticmethod
    def undistort_image(image, calibration_matrix, dist_coeff, undist_calibration_matrix, inter_method):
        """
        Returns undistorted image.
        :param image: image to undistort
        :param calibration_matrix: calibration matrix [3 x 3]
        :param dist_coeff: distortions vector
        :param undist_calibration_matrix: undistorted calibration matrix [3 x 3]
        :param inter_method: method of interpolation
        """
        if len(image.shape) == 3:
            shape = image.shape[::-1][1:]
        elif len(image.shape) == 2:
            shape = image.shape[::-1]
        else:
            raise NotImplementedError

        map_x, map_y = cv2.initUndistortRectifyMap(calibration_matrix, dist_coeff, None, undist_calibration_matrix, shape, cv2.CV_32FC1)
        undist_image = cv2.remap(image, map_x, map_y, inter_method)

        return undist_image

    @staticmethod
    def to_homogeneous(t):
        """
        Homegenize coordinates.
        :param t: cartesian coordinates
        """
        return np.concatenate((t, np.ones((len(t), 1))), axis=-1)

    @staticmethod
    def to_cartesian(t):
        """
        Dehomegenize coordinates.
        :param t: homogeneous coordinates
        """
        return t[:, :-1] / np.expand_dims(t[:, -1], -1)


    def to_norm_image_coord(self, loc_kp, calibration_matrix):
        """
        :param loc_kp: np.ndarray(N, 2), points to transform
        :param calibration_matrix: calibration matrix [3 x 3]
        """
        return (np.linalg.inv(calibration_matrix) @ self.to_homogeneous(loc_kp).T).T

    def pointcloudify_depths(self, img_depth, undist_calibration_matrix):
        """
        Transform from depth image frame to depth camera frame.
        :param img_depth: np.ndarray, depth image
        :param undist_calibration_matrix: undistorted calibration matrix [3 x 3]
        """
        shape = img_depth.shape[::-1]

        grid_x, grid_y = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]))
        grid = np.concatenate([np.expand_dims(grid_x, -1),
                               np.expand_dims(grid_y, -1)], axis=-1)

        norm_grid = self.to_norm_image_coord(grid.reshape(-1, 2), undist_calibration_matrix)

        # Raise by undistorted depth value from image plane to local camera space
        local_grid = norm_grid * np.expand_dims(img_depth.reshape(-1), axis=-1)
        return local_grid.astype(np.float32)


    def project2image(self, scene_points, undistorted_calibration_matrix):
        """
        Transform point cloud from camera coordinate frame to camera image plane.
        :param scene_points: np.ndarray(N, 3), point cloud in camera coordinate frame
        """
        return self.to_cartesian((undistorted_calibration_matrix @ scene_points.T).T)


    def depth2rgb_for_pair(self, img_depth, img_rgb, timestamp_rgb):
        """
        depth2rgb procedure for one pair of input depth and rgb images.
        Process and save depth image projected onto color image and undistorted color image.
        :param img_depth: depth image, np.ndarray([N1, N2])
        :param img_rgb: rgb image, np.ndarray([N1, N2, 3])
        :param timestamp_rgb: relative time of capturing rgb image. Used for naming output files.
        """
        img_rgb_undistorted = self.undistort_image(img_rgb, self.Kc, self.Dc, self.Kc_undistorted, cv2.INTER_LINEAR)
        img_depth_undistorted = self.undistort_image(img_depth, self.Kd, self.Dd, self.Kd_undistorted, cv2.INTER_LINEAR)

        local_depth_camera_pcd = self.pointcloudify_depths(img_depth_undistorted, self.Kd_undistorted)
        local_rgb_camera_pcd = self.to_cartesian((self.T @ self.to_homogeneous(local_depth_camera_pcd).transpose()).transpose())

        h, w = self.shape_c
        depth = local_rgb_camera_pcd[:, 2]

        proj_pcd = self.project2image(local_rgb_camera_pcd, self.Kc_undistorted)
        proj_pcd = np.round(proj_pcd).astype(int)[:, [0, 1]]

        proj_mask = (proj_pcd[:, 0] >= 0) & (proj_pcd[:, 0] < w) & (proj_pcd[:, 1] >= 0) & (proj_pcd[:, 1] < h)
        proj_pcd = proj_pcd[proj_mask, :]
        depth = depth[proj_mask]

        pcd_image = np.zeros((h, w))
        pcd_image[proj_pcd[:, 1], proj_pcd[:, 0]] = depth

        cv2.imwrite(self.output_folder + '/depth/' + timestamp_rgb + '.' + self.depth_format, pcd_image.astype(np.uint16))
        cv2.imwrite(self.output_folder + '/color/' + timestamp_rgb + '.' + self.rgb_format, img_rgb_undistorted)

    def create_timestamps_correspondance_dict(self):
        self.rgb_to_depth_timestamps_correspondance_dict = {}
        rgb_timestamps = np.array([int(path.split('.')[0]) for path in os.listdir(self.path_to_rgb_camera_images)])
        depth_timestamps = np.array([int(path.split('.')[0]) for path in os.listdir(self.path_to_depth_camera_images)])

        rgb_input_format = os.listdir(self.path_to_rgb_camera_images)[0].split('.')[1]
        depth_input_format = os.listdir(self.path_to_depth_camera_images)[0].split('.')[1]

        for ts in rgb_timestamps:
            cor_idx = np.argmin(np.abs(ts - depth_timestamps))
            if np.abs(ts - depth_timestamps[cor_idx]) < 1000:
                self.rgb_to_depth_timestamps_correspondance_dict[f'{ts:012}.{rgb_input_format}'] = f'{depth_timestamps[cor_idx]:012}.{depth_input_format}'
            else:
                print(f'Too big difference ({np.abs(ts - depth_timestamps[cor_idx])} μs) to find correspondence, rgb timestamp {ts:012} is omitted')


    def depth2rgb_for_folder(self):
        self.create_timestamps_correspondance_dict()

        for rgb_name, depth_name in tqdm(self.rgb_to_depth_timestamps_correspondance_dict.items()):
            img_rgb = cv2.imread(self.path_to_rgb_camera_images + rgb_name)
            img_depth = cv2.imread(self.path_to_depth_camera_images + depth_name, cv2.IMREAD_UNCHANGED)
            self.depth2rgb_for_pair(img_depth, img_rgb, timestamp_rgb = rgb_name.split('.')[0])



def main():
    ########### Read params from command line ###########
    parser = argparse.ArgumentParser(description='This function aligns depth to the rgb images for all rgb timestamps.\
     It returns two folders. The first contains undistorted rgb images. The second contains depth images projected to rgb camera frame coordinate system.')
    parser.add_argument('p',
                         type=str,
                         help='Path to the folder with all recordings (1m, 2s, 3s, ...), format: \'.../folder_name/\'\
                         You could specify the path as \'.../camera_name/\' if you\'d like to project depth on the color images of the same camera.\
                         No need to specify -e, -c, -d then.')
    parser.add_argument('-c',
                        '--rgb',
                         dest='rgb_camera',
                         type=str,
                         help='Name of color camera folder, format: \'1m\'')
    parser.add_argument('-d',
                        '--depth',
                        dest='depth_camera',
                        type=str,
                        help='Name of depth camera folder, format: \'1m\'')
    parser.add_argument('-e',
                        '--extr',
                        dest='ex_params',
                        type=str,
                        help='Path to extrinsics between rgb and depth camera, format: \'.../extr.json\'')
    parser.add_argument('-o',
                        '--output_folder',
                        dest='output_folder',
                        type=str,
                        help='Path to the folder, where to solve aligned images. Final structure will be as follows:\
                         \'folder_name/depth/$.png\', \'folder_name/color/$.png\'. By default will save to \'./{p}_aligned/\'')
    parser.add_argument('--depth_format',
                        dest='depth_format',
                        type=str,
                        default='png',
                        help='Format to save undistorted rgb image')
    parser.add_argument('--rgb_format',
                        dest='rgb_format',
                        type=str,
                        default='png',
                        help='Format to save undistorted depth image')
    parser.add_argument('-overwriting',
                        action='store_true',
                        help='If activated, will remove contents of specified output folder before running')

    args = parser.parse_args()

    if (args.p is not None) & (args.rgb_camera is not None) & (args.depth_camera is not None) & (args.ex_params is not None):
        path_to_depth_params = args.p + args.depth_camera + '/calib_params.json'
        path_to_rgb_params = args.p + args.rgb_camera + '/calib_params.json'
        path_to_extrinsics_params = args.ex_params
        path_to_rgb_camera_images = args.p + args.rgb_camera + '/color/'
        path_to_depth_camera_images = args.p + args.depth_camera + '/depth/'
        output_name_default = args.p.split('/')[-2] + '_' + args.depth_camera + '_' + args.rgb_camera + '_aligned'

    elif (args.p is not None) & (args.rgb_camera is None) & (args.depth_camera is None) & (args.ex_params is None):
        path_to_depth_params = args.p + 'calib_params.json'
        path_to_rgb_params = args.p + 'calib_params.json'
        path_to_extrinsics_params = args.p + 'calib_params.json'
        path_to_rgb_camera_images = args.p + 'color/'
        path_to_depth_camera_images = args.p + 'depth/'
        output_name_default = args.p.split('/')[-3] + '_' + args.p.split('/')[-2] + '_aligned'
    else:
        raise ValueError("Either only p or all(p, d, c, e) should be specified")

    output_folder = args.output_folder
    rgb_format = args.rgb_format
    depth_format = args.depth_format

    if output_folder is None:
        output_folder = output_name_default

    print(f'Output directory is: {output_folder}')

    # If folder exists and overwriting is true than delete folder and create it again
    if os.path.exists(output_folder) & args.overwriting:
        rmtree(output_folder)
        os.makedirs(output_folder + '/color')
        os.makedirs(output_folder + '/depth')
        print('Output directory will be overwrited')

    #If folder doen't exist, create it
    elif not os.path.exists(output_folder):
        os.makedirs(output_folder + '/color')
        os.makedirs(output_folder + '/depth')

    ########### Initialize rgb2depth procedure and run it ###########
    aligner = depth2rgb(path_to_depth_params=path_to_depth_params,
                        path_to_rgb_params=path_to_rgb_params,
                        path_to_extrinsics_params=path_to_extrinsics_params,
                        path_to_rgb_camera_images=path_to_rgb_camera_images,
                        path_to_depth_camera_images=path_to_depth_camera_images,
                        output_folder=output_folder,
                        rgb_format=rgb_format,
                        depth_format=rgb_format)

    aligner.depth2rgb_for_folder()


if __name__ == '__main__':
    main()
