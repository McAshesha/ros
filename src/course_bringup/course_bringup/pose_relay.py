import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from turtlesim_msgs.msg import Pose


class PoseRelay(Node):

    def __init__(self):
        super().__init__('pose_relay')
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.publisher = self.create_publisher(Pose, 'sensor_pose', qos)
        self.subscription = self.create_subscription(Pose, 'pose', self.on_pose, 10)

    def on_pose(self, message):
        self.publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = PoseRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
