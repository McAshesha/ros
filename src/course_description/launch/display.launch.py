from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    share = FindPackageShare('course_description')
    description = Command([
        FindExecutable(name='xacro'), ' ',
        PathJoinSubstitution([share, 'urdf', 'vehicle.urdf.xacro']),
        ' wheelbase:=', LaunchConfiguration('wheelbase'),
        ' track:=', LaunchConfiguration('track'),
        ' wheel_radius:=', LaunchConfiguration('wheel_radius'),
    ])
    return LaunchDescription([
        DeclareLaunchArgument('wheelbase', default_value='0.8'),
        DeclareLaunchArgument('track', default_value='0.62'),
        DeclareLaunchArgument('wheel_radius', default_value='0.12'),
        DeclareLaunchArgument('rviz', default_value='true'),
        Node(
            package='robot_state_publisher', executable='robot_state_publisher',
            output='screen', parameters=[{
                'robot_description': ParameterValue(description, value_type=str),
            }],
        ),
        Node(
            package='rviz2', executable='rviz2', output='screen',
            arguments=['-d', PathJoinSubstitution([share, 'config', 'vehicle.rviz'])],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
