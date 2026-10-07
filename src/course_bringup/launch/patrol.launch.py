from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    reliability = LaunchConfiguration('subscriber_reliability')
    sensor_topic = PathJoinSubstitution(['/', namespace, 'sensor_pose'])
    qos_file = PathJoinSubstitution([
        FindPackageShare('course_bringup'), 'config', 'qos-overrides.yaml',
    ])
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='robot_a'),
        DeclareLaunchArgument('record', default_value='false'),
        DeclareLaunchArgument('bag_dir', default_value='evidence/pr05/bag'),
        DeclareLaunchArgument('subscriber_reliability', default_value='best_effort'),
        Node(package='turtlesim', executable='turtlesim_node', output='screen'),
        Node(
            package='patrol', executable='patrol', namespace=namespace, output='screen',
            remappings=[('cmd_vel', '/turtle1/cmd_vel'), ('turtle1/pose', '/turtle1/pose')],
        ),
        Node(
            package='course_bringup', executable='pose_relay', namespace=namespace,
            output='screen', remappings=[('pose', '/turtle1/pose')],
        ),
        Node(
            package='course_bringup', executable='pose_subscriber', namespace=namespace,
            output='screen', parameters=[{'reliability': reliability}],
        ),
        ExecuteProcess(
            cmd=['ros2', 'bag', 'record', '-s', 'mcap', '-o', bag_dir,
                 '--qos-profile-overrides-path', qos_file, '--topics', sensor_topic],
            output='screen', condition=IfCondition(record),
        ),
    ])
