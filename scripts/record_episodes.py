#!/usr/bin/env python3

import argparse
import os
import time


from eve.constants import (
    DT,
    FOLLOWER_GRIPPER_JOINT_CLOSE,
    FOLLOWER_GRIPPER_JOINT_OPEN,
    FPS,
    IS_MOBILE,
    LEADER_GRIPPER_CLOSE_THRESH,
    LEADER_GRIPPER_JOINT_MID,
    START_ARM_POSE,
    TASK_CONFIGS,
)
from eve.real_env import (
    get_action,
    make_real_env
)
from eve.robot_utils import (
    get_arm_gripper_positions,
    ImageRecorder,
    move_arms,
    move_grippers,
    Recorder,
    torque_off,
    torque_on,
)
import cv2
import h5py
from interbotix_common_modules.common_robot.robot import (
    create_interbotix_global_node,
    robot_shutdown,
    robot_startup,
)
from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS
import IPython
import numpy as np
import rclpy
from tqdm import tqdm


e = IPython.embed


def opening_ceremony(
    leader_bot_left: InterbotixManipulatorXS,
    leader_bot_right: InterbotixManipulatorXS,
    follower_bot_left: InterbotixManipulatorXS,
    follower_bot_right: InterbotixManipulatorXS,
    active_arms: str
):
    """Move the robots to a pose where it is easy to start the demonstration, based on active arms."""
    if active_arms in ["both", "left"]:
        # Set operating modes and reboot gripper motors for left arms
        follower_bot_left.core.robot_reboot_motors('single', 'gripper', True)
        follower_bot_left.core.robot_set_operating_modes('group', 'arm', 'position')
        follower_bot_left.core.robot_set_operating_modes('single', 'gripper', 'current_based_position')
        leader_bot_left.core.robot_set_operating_modes('group', 'arm', 'position')
        leader_bot_left.core.robot_set_operating_modes('single', 'gripper', 'position')
        follower_bot_left.core.robot_set_motor_registers('single', 'gripper', 'current_limit', 200)
        torque_on(follower_bot_left)
        torque_on(leader_bot_left)
    
    if active_arms in ["both", "right"]:
        # Set operating modes and reboot gripper motors for right arms
        follower_bot_right.core.robot_reboot_motors('single', 'gripper', True)
        follower_bot_right.core.robot_set_operating_modes('group', 'arm', 'position')
        follower_bot_right.core.robot_set_operating_modes('single', 'gripper', 'current_based_position')
        leader_bot_right.core.robot_set_operating_modes('group', 'arm', 'position')
        leader_bot_right.core.robot_set_operating_modes('single', 'gripper', 'position')
        follower_bot_right.core.robot_set_motor_registers('single', 'gripper', 'current_limit', 200)
        torque_on(follower_bot_right)
        torque_on(leader_bot_right)

    # Move arms to starting position based on active arms
    start_arm_qpos = START_ARM_POSE[:6]
    if active_arms == "both":
        move_arms(
            [leader_bot_left, follower_bot_left, leader_bot_right, follower_bot_right],
            [start_arm_qpos] * 4,
            moving_time=1.5,
        )
        move_grippers(
            [leader_bot_left, follower_bot_left, leader_bot_right, follower_bot_right],
            [LEADER_GRIPPER_JOINT_MID, FOLLOWER_GRIPPER_JOINT_CLOSE] * 2,
            moving_time=0.5,
        )
    elif active_arms == "left":
        move_arms(
            [leader_bot_left, follower_bot_left],
            [start_arm_qpos] * 2,
            moving_time=1.5,
        )
        move_grippers(
            [leader_bot_left, follower_bot_left],
            [LEADER_GRIPPER_JOINT_MID, FOLLOWER_GRIPPER_JOINT_CLOSE],
            moving_time=0.5,
        )
    elif active_arms == "right":
        move_arms(
            [leader_bot_right, follower_bot_right],
            [start_arm_qpos] * 2,
            moving_time=1.5,
        )
        move_grippers(
            [leader_bot_right, follower_bot_right],
            [LEADER_GRIPPER_JOINT_MID, FOLLOWER_GRIPPER_JOINT_CLOSE],
            moving_time=0.5,
        )

    # Press gripper to start data collection
    if active_arms in ["both", "left"]:
        leader_bot_left.core.robot_torque_enable('single', 'gripper', False)
    if active_arms in ["both", "right"]:
        leader_bot_right.core.robot_torque_enable('single', 'gripper', False)
    
    print('Close the gripper to start')
    pressed = False
    while rclpy.ok() and not pressed:
        gripper_pos_left = get_arm_gripper_positions(leader_bot_left) if active_arms in ["both", "left"] else None
        gripper_pos_right = get_arm_gripper_positions(leader_bot_right) if active_arms in ["both", "right"] else None
        pressed = (
            (gripper_pos_left is None or gripper_pos_left < LEADER_GRIPPER_CLOSE_THRESH) and
            (gripper_pos_right is None or gripper_pos_right < LEADER_GRIPPER_CLOSE_THRESH)
        )
        time.sleep(DT/10)
    
    if active_arms in ["both", "left"]:
        torque_off(leader_bot_left)
    if active_arms in ["both", "right"]:
        torque_off(leader_bot_right)
    print('Started!')

def capture_one_episode(
    dt,
    max_timesteps,
    camera_names,
    dataset_dir,
    dataset_name,
    overwrite,
    active_arms,
    torque_base: bool = False,
):
    print(f'Dataset name: {dataset_name}')

    node = create_interbotix_global_node('eve')

    # Source of data
    leader_bot_left = InterbotixManipulatorXS(
        robot_model='wx250s',
        robot_name='leader_left',
        node=node,
        iterative_update_fk=False,
    ) if active_arms in ["both", "left"] else None
    leader_bot_right = InterbotixManipulatorXS(
        robot_model='wx250s',
        robot_name='leader_right',
        node=node,
        iterative_update_fk=False,
    ) if active_arms in ["both", "right"] else None

    env = make_real_env(
        node=node,
        active_arms=active_arms,
        setup_robots=False,
        setup_base=IS_MOBILE,
        torque_base=torque_base,
    )

    robot_startup(node)

    # Saving dataset
    if not os.path.isdir(dataset_dir):
        os.makedirs(dataset_dir)
    dataset_path = os.path.join(dataset_dir, dataset_name)
    if os.path.isfile(dataset_path) and not overwrite:
        print(f'Dataset already exists at \n{dataset_path}\nHint: set overwrite to True.')
        exit()

    # Move robots to starting pose and wait for gripper closure
    opening_ceremony(
        leader_bot_left,
        leader_bot_right,
        env.follower_bot_left,
        env.follower_bot_right,
        active_arms
    )

    # Data collection
    ts = env.reset(fake=True)
    timesteps = [ts]
    actions = []
    actual_dt_history = []
    time0 = time.time()
    DT = 1 / FPS
    for t in tqdm(range(max_timesteps)):
        t0 = time.time()
        action = get_action(leader_bot_left, leader_bot_right, active_arms)
        t1 = time.time()
        ts = env.step(action)
        t2 = time.time()
        timesteps.append(ts)
        actions.append(action)
        actual_dt_history.append([t0, t1, t2])
        time.sleep(max(0, DT - (time.time() - t0)))
    print(f'Avg fps: {max_timesteps / (time.time() - time0)}')

    # Torque on both leader bots if applicable
    if active_arms in ["both", "left"]:
        torque_on(leader_bot_left)
        # Open follower grippers
        env.follower_bot_left.core.robot_set_operating_modes('single', 'gripper', 'position')
        move_grippers(
            [env.follower_bot_left],
            [FOLLOWER_GRIPPER_JOINT_CLOSE],
            moving_time=0.5
        )
    if active_arms in ["both", "right"]:
        torque_on(leader_bot_right)
        env.follower_bot_right.core.robot_set_operating_modes('single', 'gripper', 'position')
        move_grippers(
            [env.follower_bot_right],
            [FOLLOWER_GRIPPER_JOINT_CLOSE],
            moving_time=0.5
        )

    freq_mean = print_dt_diagnosis(actual_dt_history)
    if freq_mean < 30:
        print(f'\n\nfreq_mean is {freq_mean}, lower than 30, re-collecting... \n\n\n\n')
        return False

    """
    For each timestep:
    observations
    - images
        - cam_high          (480, 640, 3) 'uint8'
        - cam_low           (480, 640, 3) 'uint8'
        - cam_left_wrist    (480, 640, 3) 'uint8'
        - cam_right_wrist   (480, 640, 3) 'uint8'
    - qpos                  (14,)         'float64'
    - qvel                  (14,)         'float64'

    action                  (14,)         'float64'
    base_action             (2,)          'float64'
    """

    data_dict = {
        '/observations/qpos': [],
        '/observations/qvel': [],
        '/observations/effort': [],
        '/action': [],
    }
    if IS_MOBILE:
        data_dict['/base_action'] = []
    for cam_name in camera_names:
        data_dict[f'/observations/images/{cam_name}'] = []

    # len(action): max_timesteps, len(time_steps): max_timesteps + 1
    while actions:
        action = actions.pop(0)
        ts = timesteps.pop(0)
        data_dict['/observations/qpos'].append(ts.observation['qpos'])
        data_dict['/observations/qvel'].append(ts.observation['qvel'])
        data_dict['/observations/effort'].append(ts.observation['effort'])
        data_dict['/action'].append(action)
        if IS_MOBILE:
            data_dict['/base_action'].append(ts.observation['base_vel'])
        for cam_name in camera_names:
            data_dict[f'/observations/images/{cam_name}'].append(
                ts.observation['images'][cam_name]
            )

    COMPRESS = False

    if COMPRESS:
        # JPEG compression
        t0 = time.time()
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]  # tried as low as 20, seems fine
        compressed_len = []
        for cam_name in camera_names:
            image_list = data_dict[f'/observations/images/{cam_name}']
            compressed_list = []
            compressed_len.append([])
            for image in image_list:
                # 0.02 sec # cv2.imdecode(encoded_image, 1)
                result, encoded_image = cv2.imencode('.jpg', image, encode_param)
                compressed_list.append(encoded_image)
                compressed_len[-1].append(len(encoded_image))
            data_dict[f'/observations/images/{cam_name}'] = compressed_list
        print(f'compression: {time.time() - t0:.2f}s')

        # Pad so it has same length
        t0 = time.time()
        compressed_len = np.array(compressed_len)
        padded_size = compressed_len.max()
        for cam_name in camera_names:
            compressed_image_list = data_dict[f'/observations/images/{cam_name}']
            padded_compressed_image_list = []
            for compressed_image in compressed_image_list:
                padded_compressed_image = np.zeros(padded_size, dtype='uint8')
                image_len = len(compressed_image)
                padded_compressed_image[:image_len] = compressed_image
                padded_compressed_image_list.append(padded_compressed_image)
            data_dict[f'/observations/images/{cam_name}'] = padded_compressed_image_list
        print(f'padding: {time.time() - t0:.2f}s')

    # Save to HDF5
    t0 = time.time()
    with h5py.File(dataset_path + '.hdf5', 'w', rdcc_nbytes=1024**2*2) as root:
        root.attrs['sim'] = False
        root.attrs['compress'] = COMPRESS
        obs = root.create_group('observations')
        image = obs.create_group('images')
        for cam_name in camera_names:
            if COMPRESS:
                _ = image.create_dataset(cam_name, (max_timesteps, padded_size), dtype='uint8',
                                         chunks=(1, padded_size), )
            else:
                _ = image.create_dataset(cam_name, (max_timesteps, 480, 640, 3), dtype='uint8',
                                         chunks=(1, 480, 640, 3), )
        _ = obs.create_dataset('qpos', (max_timesteps, 14))
        _ = obs.create_dataset('qvel', (max_timesteps, 14))
        _ = obs.create_dataset('effort', (max_timesteps, 14))
        _ = root.create_dataset('action', (max_timesteps, 14))
        if IS_MOBILE:
            _ = root.create_dataset('base_action', (max_timesteps, 2))

        for name, array in data_dict.items():
            root[name][...] = array

        if COMPRESS:
            _ = root.create_dataset('compress_len', (len(camera_names), max_timesteps))
            root['/compress_len'][...] = compressed_len

    print(f'Saving: {time.time() - t0:.1f} secs')

    robot_shutdown()
    return True


def main(args: dict):
    task_config = TASK_CONFIGS[args['task_name']]
    dataset_dir = task_config['dataset_dir']
    max_timesteps = task_config['episode_len']
    camera_names = task_config['camera_names']

    torque_base = args.get('enable_base_torque', False)

    if args['episode_idx'] is not None:
        episode_idx = args['episode_idx']
    else:
        episode_idx = get_auto_index(dataset_dir)
    overwrite = True

    dataset_name = f'episode_{episode_idx}'
    print(dataset_name + '\n')
    while True:
        is_healthy = capture_one_episode(
            DT,
            max_timesteps,
            camera_names,
            dataset_dir,
            dataset_name,
            overwrite,
            args["arm"],
            torque_base,
        )
        if is_healthy:
            break


def get_auto_index(dataset_dir, dataset_name_prefix='', data_suffix='hdf5'):
    max_idx = 1000
    if not os.path.isdir(dataset_dir):
        os.makedirs(dataset_dir)
    for i in range(max_idx+1):
        if not os.path.isfile(
            os.path.join(dataset_dir, f'{dataset_name_prefix}episode_{i}.{data_suffix}')
        ):
            return i
    raise Exception(f'Error getting auto index, or more than {max_idx} episodes')


def print_dt_diagnosis(actual_dt_history):
    actual_dt_history = np.array(actual_dt_history)
    get_action_time = actual_dt_history[:, 1] - actual_dt_history[:, 0]
    step_env_time = actual_dt_history[:, 2] - actual_dt_history[:, 1]
    total_time = actual_dt_history[:, 2] - actual_dt_history[:, 0]

    dt_mean = np.mean(total_time)
    # dt_std = np.std(total_time)
    freq_mean = 1 / dt_mean
    print((
        f'Avg freq: {freq_mean:.2f} Get action: {np.mean(get_action_time):.3f} '
        f'Step env: {np.mean(step_env_time):.3f}')
    )
    return freq_mean


def debug():
    print(f'====== Debug mode ======')
    recorder = Recorder('right', is_debug=True)
    image_recorder = ImageRecorder(init_node=False, is_debug=True)
    while True:
        time.sleep(1)
        recorder.print_diagnostics()
        image_recorder.print_diagnostics()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--task_name',
        action='store',
        type=str,
        help='Task name.',
        required=True,
    )
    parser.add_argument(
        '--episode_idx',
        action='store',
        type=int,
        help='Episode index.',
        default=None,
        required=False,
    )
    parser.add_argument(
        '-b', '--enable_base_torque',
        action='store_true',
        help=(
            'If set, mobile base will be torqued on during episode recording, allowing the use of'
            ' a joystick controller or some other manual method.'
        ),
    )
    parser.add_argument(
        '--arm',
        type=str,
        default='both',
        help='Specify which arms to activate: both, left, or right.'
    )
    main(vars(parser.parse_args()))
    # debug()
