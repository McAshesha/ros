from pathlib import Path

from course_bringup.pose_relay import PoseRelay
from course_bringup.pose_subscriber import PoseSubscriber, subscriber_qos
import pytest
import rclpy
from rclpy.qos import DurabilityPolicy, HistoryPolicy, ReliabilityPolicy
from turtlesim_msgs.msg import Pose


@pytest.mark.parametrize('name, policy', [
    ('reliable', ReliabilityPolicy.RELIABLE),
    ('best_effort', ReliabilityPolicy.BEST_EFFORT),
])
def test_subscriber_profile(name, policy):
    qos = subscriber_qos(name)
    assert qos.reliability == policy
    assert qos.history == HistoryPolicy.KEEP_LAST
    assert qos.durability == DurabilityPolicy.VOLATILE
    assert qos.depth == 10


def test_invalid_reliability():
    with pytest.raises(ValueError):
        subscriber_qos('typo')


def test_nodes_use_relative_topics_and_best_effort():
    rclpy.init(args=['--ros-args', '-r', '__ns:=/test_robot'])
    relay = PoseRelay()
    subscriber = PoseSubscriber()
    try:
        assert relay.subscription.topic_name == '/test_robot/pose'
        assert relay.publisher.topic_name == '/test_robot/sensor_pose'
        assert relay.publisher.qos_profile.reliability == ReliabilityPolicy.BEST_EFFORT
        assert subscriber.subscription.topic_name == '/test_robot/sensor_pose'
        subscriber.on_pose(Pose())
        assert subscriber.received == 1
    finally:
        relay.destroy_node()
        subscriber.destroy_node()
        rclpy.try_shutdown()


def test_replay_override_matches_installed_config():
    root = Path(__file__).resolve().parents[3]
    assert (root / 'config/qos-overrides.yaml').read_text() == (
        root / 'src/course_bringup/config/qos-overrides.yaml'
    ).read_text()
