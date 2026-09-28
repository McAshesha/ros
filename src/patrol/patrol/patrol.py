import math

from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.node import Node
from turtlesim_msgs.msg import Pose

PATROL_LINEAR_X = 0.5
PATROL_ANGULAR_Z = 0.3
PATROL_PUBLISH_HZ = 10.0

# name -> (min, max), inclusive
PARAMETER_LIMITS = {
    'linear_speed': (0.0, 1.0),
    'turn_rate': (-1.0, 1.0),
    'publish_hz': (1.0, 30.0),
}


def choose_command(pose, linear_speed=PATROL_LINEAR_X, turn_rate=PATROL_ANGULAR_Z):
    """Return the Twist to publish for the latest pose (None until one arrives)."""
    command = Twist()
    if pose is None:
        return command
    command.linear.x = linear_speed
    command.angular.z = turn_rate
    return command


def validate_values(publish_hz, linear_speed, turn_rate):
    """Return (ok, reason) for a proposed set of parameter values."""
    values = {
        'publish_hz': publish_hz,
        'linear_speed': linear_speed,
        'turn_rate': turn_rate,
    }
    for name, value in values.items():
        low, high = PARAMETER_LIMITS[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False, f'{name} must be a number, got {value!r}'
        if not math.isfinite(value) or not low <= value <= high:
            return False, f'{name}={value} is outside [{low}, {high}]'
    return True, ''


class Patrol(Node):

    def __init__(self):
        super().__init__('patrol')
        self.declare_parameter('linear_speed', PATROL_LINEAR_X)
        self.declare_parameter('turn_rate', PATROL_ANGULAR_Z)
        self.declare_parameter('publish_hz', PATROL_PUBLISH_HZ)
        self.linear_speed = self.get_parameter('linear_speed').value
        self.turn_rate = self.get_parameter('turn_rate').value
        self.publish_hz = self.get_parameter('publish_hz').value
        ok, reason = validate_values(self.publish_hz, self.linear_speed, self.turn_rate)
        if not ok:
            raise ValueError(reason)

        self.latest_pose = None
        self.pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self.on_pose, 10,
        )
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(1.0 / self.publish_hz, self.on_timer)
        self.add_on_set_parameters_callback(self.validate)
        self.add_post_set_parameters_callback(self.apply)

    def validate(self, parameters):
        """Check the whole proposed set; must not change the node state."""
        proposed = {p.name: p.value for p in parameters}
        ok, reason = validate_values(
            proposed.get('publish_hz', self.publish_hz),
            proposed.get('linear_speed', self.linear_speed),
            proposed.get('turn_rate', self.turn_rate),
        )
        return SetParametersResult(successful=ok, reason=reason)

    def apply(self, parameters):
        """Apply an accepted set: update fields, rebuild the timer on a new rate."""
        old_hz = self.publish_hz
        for parameter in parameters:
            if parameter.name in PARAMETER_LIMITS:
                setattr(self, parameter.name, parameter.value)
        if self.publish_hz != old_hz:
            self.timer.cancel()
            self.destroy_timer(self.timer)
            self.timer = self.create_timer(1.0 / self.publish_hz, self.on_timer)
            self.get_logger().info(
                f'publish_hz {old_hz} -> {self.publish_hz}, '
                f'timer period {1.0 / self.publish_hz:.3f} s'
            )

    def on_pose(self, message):
        self.latest_pose = message

    def on_timer(self):
        self.cmd_pub.publish(
            choose_command(self.latest_pose, self.linear_speed, self.turn_rate)
        )


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
