import os
import launch
import launch_ros.actions
from ament_index_python.packages import get_package_share_directory
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Get the path to the robot's URDF file
    urdf_file = os.path.join(
        get_package_share_directory('fairino_description'),
        'urdf',
        'fr5v6_gazebo.urdf'
    )

    # Ensure the URDF file exists
    assert os.path.exists(urdf_file), "URDF file does not exist: " + urdf_file

    # Launch Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ]),
        launch_arguments={'gz_args': ''}.items()
    )

    # Spawn the robot in Gazebo
    spawn_entity = launch_ros.actions.Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-file', urdf_file,
            '-name', 'my_robot',
            '-x', '0', '-y', '0', '-z', '1'
        ],
        output='screen'
    )

    return launch.LaunchDescription([
        gazebo,
        spawn_entity
    ])
