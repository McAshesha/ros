from patrol.patrol import choose_command
from turtlesim_msgs.msg import Pose


def test_no_pose_gives_zero_command():
    command = choose_command(None)
    assert command.linear.x == 0.0
    assert command.linear.y == 0.0
    assert command.linear.z == 0.0
    assert command.angular.x == 0.0
    assert command.angular.y == 0.0
    assert command.angular.z == 0.0


def test_pose_gives_patrol_command():
    pose = Pose(x=5.5, y=5.5, theta=0.0)
    command = choose_command(pose)
    assert command.linear.x == 0.5
    assert command.angular.z == 0.3
    assert command.linear.y == 0.0
    assert command.linear.z == 0.0
    assert command.angular.x == 0.0
    assert command.angular.y == 0.0


def test_command_does_not_depend_on_pose_values():
    first = choose_command(Pose(x=1.0, y=1.0, theta=3.0))
    second = choose_command(Pose(x=10.0, y=10.0, theta=-3.0))
    assert first == second
