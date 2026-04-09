#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():

    # Package names
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')  # Gazebo ROS package
    pkg_fairino_description = get_package_share_directory('fairino_description')  # Your robot description package
    pkg_fairino_gazebo = get_package_share_directory('fairino_description')  # Your Gazebo package (if you have one)

    # Set Gazebo model and plugin paths
    install_dir = get_package_prefix('fairino_description')
    gazebo_models_path = os.path.join(pkg_fairino_description, 'models')  # Path to your robot's models

    # Update GAZEBO_MODEL_PATH and GAZEBO_PLUGIN_PATH
    if 'GAZEBO_MODEL_PATH' in os.environ:
        os.environ['GAZEBO_MODEL_PATH'] += ':' + install_dir + '/share' + ':' + gazebo_models_path
    else:
        os.environ['GAZEBO_MODEL_PATH'] = install_dir + "/share" + ':' + gazebo_models_path

    if 'GAZEBO_PLUGIN_PATH' in os.environ:
        os.environ['GAZEBO_PLUGIN_PATH'] += ':' + install_dir + '/lib'
    else:
        os.environ['GAZEBO_PLUGIN_PATH'] = install_dir + '/lib'

    print("GAZEBO MODELS PATH==" + str(os.environ["GAZEBO_MODEL_PATH"]))
    print("GAZEBO PLUGINS PATH==" + str(os.environ["GAZEBO_PLUGIN_PATH"]))

    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py'),
        )
    )

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': open(os.path.join(pkg_fairino_description, 'urdf', 'fr5v6_hitbot.urdf'), 'r').read()
        }]
    )

    # Spawn the robot in Gazebo
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_fr5v6_hitbot',
        output='screen',
        arguments=[
            '-entity', 'fr5v6_hitbot',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1'
        ]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=[os.path.join(pkg_fairino_gazebo, 'worlds', 'empty.world'), ''],
            description='SDF world file'
        ),
        gazebo,
        robot_state_publisher,
        spawn_robot
    ])
