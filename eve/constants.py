# flake8: noqa

import os

### Task parameters

# Set to 'true' for Mobile ALOHA, 'false' for Stationary ALOHA
IS_MOBILE = os.environ.get('INTERBOTIX_ALOHA_IS_MOBILE', 'true').lower() == 'true'

COLOR_IMAGE_TOPIC_NAME = '{}/camera/color/image_rect_raw'  # for RealSense cameras

# DATA_DIR = os.path.expanduser('~/aloha_data')
DATA_DIR = "/home/rl2-bonjour/interbotix_ws/src/aloha-ros2/scripts/data"
# DATA_DIR = "/media/rl2-bonjour/data/EgoplayData"

### ALOHA Fixed Constants
DT = 0.02

try:
    from rclpy.duration import Duration
    from rclpy.constants import S_TO_NS
    DT_DURATION = Duration(seconds=0, nanoseconds=DT * S_TO_NS)
except ImportError:
    pass

FPS = 50
JOINT_NAMES = ['waist', 'shoulder', 'elbow', 'forearm_roll', 'wrist_angle', 'wrist_rotate']
START_ARM_POSE = [
    0.0, -0.96, 1.16, 0.0, -0.3, 0.0, 0.02239, -0.02239,
    0.0, -0.96, 1.16, 0.0, -0.3, 0.0, 0.02239, -0.02239,
]

LEADER_GRIPPER_CLOSE_THRESH = -0.3

# Left finger position limits (qpos[7]), right_finger = -1 * left_finger
LEADER_GRIPPER_POSITION_OPEN = 0.0323
LEADER_GRIPPER_POSITION_CLOSE = 0.0185

FOLLOWER_GRIPPER_POSITION_OPEN = 0.0579
FOLLOWER_GRIPPER_POSITION_CLOSE = 0.0440

# Gripper joint limits (qpos[6])
LEADER_GRIPPER_JOINT_OPEN = 0.03
# LEADER_GRIPPER_JOINT_CLOSE = -0.0552
LEADER_GRIPPER_JOINT_CLOSE = -0.4

FOLLOWER_GRIPPER_JOINT_OPEN = 1.5
FOLLOWER_GRIPPER_JOINT_CLOSE = 0.5 #0.3

### Helper functions

LEADER_GRIPPER_POSITION_NORMALIZE_FN = lambda x: (x - LEADER_GRIPPER_POSITION_CLOSE) / (LEADER_GRIPPER_POSITION_OPEN - LEADER_GRIPPER_POSITION_CLOSE)
FOLLOWER_GRIPPER_POSITION_NORMALIZE_FN = lambda x: (x - FOLLOWER_GRIPPER_POSITION_CLOSE) / (FOLLOWER_GRIPPER_POSITION_OPEN - FOLLOWER_GRIPPER_POSITION_CLOSE)
LEADER_GRIPPER_POSITION_UNNORMALIZE_FN = lambda x: x * (LEADER_GRIPPER_POSITION_OPEN - LEADER_GRIPPER_POSITION_CLOSE) + LEADER_GRIPPER_POSITION_CLOSE
FOLLOWER_GRIPPER_POSITION_UNNORMALIZE_FN = lambda x: x * (FOLLOWER_GRIPPER_POSITION_OPEN - FOLLOWER_GRIPPER_POSITION_CLOSE) + FOLLOWER_GRIPPER_POSITION_CLOSE
LEADER2FOLLOWER_POSITION_FN = lambda x: FOLLOWER_GRIPPER_POSITION_UNNORMALIZE_FN(LEADER_GRIPPER_POSITION_NORMALIZE_FN(x))

LEADER_GRIPPER_JOINT_NORMALIZE_FN = lambda x: (x - LEADER_GRIPPER_JOINT_CLOSE) / (LEADER_GRIPPER_JOINT_OPEN - LEADER_GRIPPER_JOINT_CLOSE)
FOLLOWER_GRIPPER_JOINT_NORMALIZE_FN = lambda x: (x - FOLLOWER_GRIPPER_JOINT_CLOSE) / (FOLLOWER_GRIPPER_JOINT_OPEN - FOLLOWER_GRIPPER_JOINT_CLOSE)
LEADER_GRIPPER_JOINT_UNNORMALIZE_FN = lambda x: x * (LEADER_GRIPPER_JOINT_OPEN - LEADER_GRIPPER_JOINT_CLOSE) + LEADER_GRIPPER_JOINT_CLOSE
FOLLOWER_GRIPPER_JOINT_UNNORMALIZE_FN = lambda x: x * (FOLLOWER_GRIPPER_JOINT_OPEN - FOLLOWER_GRIPPER_JOINT_CLOSE) + FOLLOWER_GRIPPER_JOINT_CLOSE
LEADER2FOLLOWER_JOINT_FN = lambda x: FOLLOWER_GRIPPER_JOINT_UNNORMALIZE_FN(LEADER_GRIPPER_JOINT_NORMALIZE_FN(x))

LEADER_GRIPPER_VELOCITY_NORMALIZE_FN = lambda x: x / (LEADER_GRIPPER_POSITION_OPEN - LEADER_GRIPPER_POSITION_CLOSE)
FOLLOWER_GRIPPER_VELOCITY_NORMALIZE_FN = lambda x: x / (FOLLOWER_GRIPPER_POSITION_OPEN - FOLLOWER_GRIPPER_POSITION_CLOSE)

LEADER_POS2JOINT = lambda x: LEADER_GRIPPER_POSITION_NORMALIZE_FN(x) * (LEADER_GRIPPER_JOINT_OPEN - LEADER_GRIPPER_JOINT_CLOSE) + LEADER_GRIPPER_JOINT_CLOSE
LEADER_JOINT2POS = lambda x: LEADER_GRIPPER_POSITION_UNNORMALIZE_FN((x - LEADER_GRIPPER_JOINT_CLOSE) / (LEADER_GRIPPER_JOINT_OPEN - LEADER_GRIPPER_JOINT_CLOSE))
FOLLOWER_POS2JOINT = lambda x: FOLLOWER_GRIPPER_POSITION_NORMALIZE_FN(x) * (FOLLOWER_GRIPPER_JOINT_OPEN - FOLLOWER_GRIPPER_JOINT_CLOSE) + FOLLOWER_GRIPPER_JOINT_CLOSE
FOLLOWER_JOINT2POS = lambda x: FOLLOWER_GRIPPER_POSITION_UNNORMALIZE_FN((x - FOLLOWER_GRIPPER_JOINT_CLOSE) / (FOLLOWER_GRIPPER_JOINT_OPEN - FOLLOWER_GRIPPER_JOINT_CLOSE))

LEADER_GRIPPER_JOINT_MID = (LEADER_GRIPPER_JOINT_OPEN + LEADER_GRIPPER_JOINT_CLOSE)/2

### Real hardware task configurations

TASK_CONFIGS = {

    ### Template
    # 'aloha_template':{
    #     'dataset_dir': [
    #         DATA_DIR + '/aloha_template',
    #         DATA_DIR + '/aloha_template_subtask',
    #         DATA_DIR + '/aloha_template_other_subtask',
    #     ], # only the first entry in dataset_dir is used for eval
    #     'stats_dir': [
    #         DATA_DIR + '/aloha_template',
    #     ],
    #     'sample_weights': [6, 1, 1],
    #     'train_ratio': 0.99, # ratio of train data from the first dataset_dir
    #     'episode_len': 1500,
    #     'camera_names': ['cam_high', 'cam_left_wrist', 'cam_right_wrist']
    # },

    'aloha_mobile_hello_aloha':{
        'dataset_dir': DATA_DIR + '/aloha_mobile_hello_aloha',
        'episode_len': 800,
        'camera_names': ['cam_high', 'cam_left_wrist', 'cam_right_wrist']
    },

    'aloha_mobile_dummy':{
        'dataset_dir': DATA_DIR + '/aloha_mobile_dummy',
        'episode_len': 1000,
        'camera_names': ['cam_high', 'cam_left_wrist', 'cam_right_wrist']
    },

    'aloha_stationary_hello_aloha':{
        'dataset_dir': DATA_DIR + '/aloha_stationary_hello_aloha',
        'episode_len': 800,
        'camera_names': ['cam_high', 'cam_left_wrist', 'cam_right_wrist']
    },

    'aloha_stationary_dummy':{
        'dataset_dir': DATA_DIR + '/aloha_stationary_dummy',
        'episode_len': 800,
        'camera_names': ['cam_high', 'cam_left_wrist', 'cam_right_wrist']
    },
    'OBOO_ROBOTWA_BIMAN':{
        'dataset_dir': DATA_DIR + '/OBOO_ROBOTWA_BIMAN',
        'episode_len': 1000,
        'camera_names': ['cam_high', 'cam_left_wrist', 'cam_right_wrist']
    },
    'OBOO_ROBOTWA_LEFT':{
        'dataset_dir': DATA_DIR + '/OBOO_ROBOTWA_LEFT',
        'episode_len': 1000,
        'camera_names': ['cam_high', 'cam_left_wrist']
    },
    'OBOO_ROBOTWA':{
        'dataset_dir': DATA_DIR + '/OBOO_ROBOTWA',
        'episode_len': 3000,
        'camera_names': ['cam_high', 'cam_right_wrist']
    },
    'OBOO_ROBOTWA_RIGHTTABLE':{
        'dataset_dir': DATA_DIR + '/OBOO_ROBOTWA_RIGHTTABLE',
        'episode_len': 3000,
        'camera_names': ['cam_high', 'cam_right_wrist']
    },
    'ROBOTWA_CLOTHFOLD':{
        'dataset_dir': DATA_DIR + '/ROBOTWA_CLOTHFOLD',
        'episode_len': 5000,
        'camera_names': ['cam_high', 'cam_right_wrist', 'cam_left_wrist']
    },
    'ROBOTWA_GROCERIES':{
        'dataset_dir': DATA_DIR + '/ROBOTWA_GROCERIES',
        'episode_len': 6000,
        'camera_names': ['cam_high', 'cam_right_wrist', 'cam_left_wrist']
    },
    'DEBUG':{
        'dataset_dir': DATA_DIR + '/DEBUG',
        'episode_len': 700,
        'camera_names': ['cam_high']
    },
    'CALIBRATE':{
        'dataset_dir': DATA_DIR + '/CALIBRATE',
        'episode_len': 2000,
        'camera_names': ['cam_high']
    },
    'DEBUG_ROBOTWA_BLACK_TABLE': {
        'dataset_dir': DATA_DIR + '/DEBUG_ROBOTWA_BLACK_TABLE',
        'episode_len': 6000,
        'camera_names': ['cam_high', 'cam_right_wrist']
    },
    'ROBOTWA_SMALLCLOTHFOLD_DARKBLUE':{
        'dataset_dir': DATA_DIR + '/ROBOTWA_SMALLCLOTHFOLD_DARKBLUE',
        'episode_len': 5000,
        'camera_names': ['cam_high', 'cam_right_wrist', 'cam_left_wrist']
    },
    'ROBOTWA_SMALLCLOTHFOLD_WHITE':{
        'dataset_dir': DATA_DIR + '/ROBOTWA_SMALLCLOTHFOLD_WHITE',
        'episode_len': 5000,
        'camera_names': ['cam_high', 'cam_right_wrist', 'cam_left_wrist']
    },
    'ROBOTWA_SMALLCLOTHFOLD_GREY':{
        'dataset_dir': DATA_DIR + '/ROBOTWA_SMALLCLOTHFOLD_GREY',
        'episode_len': 5000,
        'camera_names': ['cam_high', 'cam_right_wrist', 'cam_left_wrist']
    },
    'ROBOTWA_SMALLCLOTHFOLD_RED':{
        'dataset_dir': DATA_DIR + '/ROBOTWA_SMALLCLOTHFOLD_RED',
        # 'dataset_dir': '/media/rl2-bonjour/data/EgoplayData' + '/ROBOTWA_SMALLCLOTHFOLD_RED',
        'episode_len': 5000,
        'camera_names': ['cam_high', 'cam_right_wrist', 'cam_left_wrist']
    },
    'ROBOTWA_SMALLCLOTHFOLD_WHITE_LONGSLEEVE':{
        'dataset_dir': DATA_DIR + '/ROBOTWA_SMALLCLOTHFOLD_WHITE_LONGSLEEVE',
        # 'dataset_dir': '/media/rl2-bonjour/data/EgoplayData' + '/ROBOTWA_SMALLCLOTHFOLD_RED',
        'episode_len': 5000,
        'camera_names': ['cam_high', 'cam_right_wrist', 'cam_left_wrist']
    },
    'ROBOTWA_SMALLCLOTHFOLD_DARKBLUE_LONGSLEEVE':{
        'dataset_dir': DATA_DIR + '/ROBOTWA_SMALLCLOTHFOLD_DARKBLUE_LONGSLEEVE',
        # 'dataset_dir': '/media/rl2-bonjour/data/EgoplayData' + '/ROBOTWA_SMALLCLOTHFOLD_RED',
        'episode_len': 5000,
        'camera_names': ['cam_high', 'cam_right_wrist', 'cam_left_wrist']
    },
    'ROBOTWA_SORTING':{
        'dataset_dir': DATA_DIR + '/ROBOTWA_SORTING',
        'episode_len': 1500,
        'camera_names': ['cam_high', 'cam_right_wrist']
    },
    'OBOO_ROBOTWA_EXTRA_HOUR':{
        'dataset_dir': DATA_DIR + '/OBOO_ROBOTWA_EXTRA_HOUR',
        'episode_len': 3000,
        'camera_names': ['cam_high', 'cam_right_wrist']
    },
    'OBOO_ROBOTWA_LANG':{
        'dataset_dir': DATA_DIR + '/OBOO_ROBOTWA_LANG',
        'episode_len': 400,
        'camera_names': ['cam_high', 'cam_right_wrist']
    },
    'ROBOTWA_COFFEE':{
        'dataset_dir': DATA_DIR + '/ROBOTWA_COFFEE',
        'episode_len': 5000,
        'camera_names': ['cam_high', 'cam_right_wrist', 'cam_left_wrist']
    },
}
