import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

# this is the function launch system will look for
def generate_launch_description():

    ####### DATA INPUT ##########
    urdf_file = 'fairino20_v6_palletizing.urdf'  # Name of your URDF file
    package_description = "fairino_description"  # Name of your package

    ####### DATA INPUT END ##########
    print("Fetching URDF ==>")

    # Get the full path to the URDF file
    robot_desc_path = os.path.join(get_package_share_directory(package_description), "urdf", urdf_file)

    # Read the URDF file content
    with open(robot_desc_path, 'r') as file:
        robot_description = file.read()

    # Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher_node',
        emulate_tty=True,
        parameters=[{'use_sim_time': True, 'robot_description': robot_description}],
        output="screen"
    )

    # Joint State Publisher GUI
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui_node',
        output="screen"
    )

    # RVIZ Configuration
    rviz_config_dir = os.path.join(get_package_share_directory(package_description), 'rviz', 'urdf_vis.rviz')

    rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
            name='rviz_node',
            parameters=[{'use_sim_time': True}],
            arguments=['-d', rviz_config_dir])

    # Create and return launch description object
    return LaunchDescription(
        [            
            robot_state_publisher_node,
            joint_state_publisher_gui_node,  # Add this line
            rviz_node
        ]
    )