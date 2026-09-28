import math

from patrol.patrol import Patrol
import pytest
import rclpy
from rclpy.parameter import Parameter


@pytest.fixture
def node():
    rclpy.init()
    patrol = Patrol()
    yield patrol
    patrol.destroy_node()
    rclpy.try_shutdown()


def set_hz(node, value):
    return node.set_parameters_atomically([Parameter('publish_hz', value=value)])


def test_defaults(node):
    assert node.get_parameter('linear_speed').value == 0.5
    assert node.get_parameter('turn_rate').value == 0.3
    assert node.get_parameter('publish_hz').value == 10.0
    assert node.timer.timer_period_ns == 100_000_000


def test_rate_change_replaces_timer(node):
    old_timer = node.timer
    assert set_hz(node, 5.0).successful
    assert node.publish_hz == 5.0
    assert node.timer is not old_timer
    assert node.timer.timer_period_ns == 200_000_000
    assert list(node.timers) == [node.timer]


@pytest.mark.parametrize('bad_hz', [0.0, -1.0, math.nan])
def test_bad_rate_keeps_value_and_timer(node, bad_hz):
    assert set_hz(node, 5.0).successful
    old_timer = node.timer
    result = set_hz(node, bad_hz)
    assert not result.successful
    assert result.reason.startswith('publish_hz')
    assert node.get_parameter('publish_hz').value == 5.0
    assert node.publish_hz == 5.0
    assert node.timer is old_timer
    assert node.timer.timer_period_ns == 200_000_000
    assert list(node.timers) == [old_timer]


def test_speed_change_keeps_timer(node):
    old_timer = node.timer
    result = node.set_parameters_atomically([
        Parameter('linear_speed', value=0.8),
        Parameter('turn_rate', value=-0.5),
    ])
    assert result.successful
    assert (node.linear_speed, node.turn_rate) == (0.8, -0.5)
    assert node.timer is old_timer


def test_bad_set_is_rejected_as_a_whole(node):
    result = node.set_parameters_atomically([
        Parameter('linear_speed', value=0.8),
        Parameter('publish_hz', value=0.0),
    ])
    assert not result.successful
    assert node.linear_speed == 0.5
    assert node.get_parameter('linear_speed').value == 0.5
