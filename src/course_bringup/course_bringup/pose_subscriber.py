import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from turtlesim_msgs.msg import Pose


def subscriber_qos(reliability):
    """Build the requested profile, rejecting misspelled policies."""
    policies = {
        'reliable': ReliabilityPolicy.RELIABLE,
        'best_effort': ReliabilityPolicy.BEST_EFFORT,
    }
    if reliability not in policies:
        raise ValueError('reliability must be reliable or best_effort')
    return QoSProfile(depth=10, reliability=policies[reliability])


class PoseSubscriber(Node):

    def __init__(self):
        super().__init__('pose_subscriber')
        self.declare_parameter('reliability', 'best_effort')
        qos = subscriber_qos(self.get_parameter('reliability').value)
        self.received = 0
        self.subscription = self.create_subscription(Pose, 'sensor_pose', self.on_pose, qos)
        self.timer = self.create_timer(1.0, self.report_count)

    def on_pose(self, message):
        self.received += 1

    def report_count(self):
        self.get_logger().info(f'received={self.received}')


def main(args=None):
    rclpy.init(args=args)
    node = PoseSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
