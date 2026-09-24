from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from turtlesim_msgs.msg import Pose

PATROL_LINEAR_X = 0.5
PATROL_ANGULAR_Z = 0.3


def choose_command(pose):
    """Return the Twist to publish for the latest pose (None until one arrives)."""
    command = Twist()
    if pose is None:
        return command
    command.linear.x = PATROL_LINEAR_X
    command.angular.z = PATROL_ANGULAR_Z
    return command


class Patrol(Node):

    def __init__(self):
        super().__init__('patrol')
        self.latest_pose = None
        self.pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self.on_pose, 10,
        )
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.on_timer)

    def on_pose(self, message):
        self.latest_pose = message

    def on_timer(self):
        self.cmd_pub.publish(choose_command(self.latest_pose))


def main(args=None):
    rclpy.init(args=args)
    node = Patrol()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
