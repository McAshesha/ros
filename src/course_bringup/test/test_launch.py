import importlib.util
from pathlib import Path

from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch_ros.actions import Node


def test_launch_arguments_and_conditional_recorder():
    path = Path(__file__).resolve().parents[1] / 'launch/patrol.launch.py'
    spec = importlib.util.spec_from_file_location('patrol_launch', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    entities = module.generate_launch_description().entities
    arguments = [e.name for e in entities if isinstance(e, DeclareLaunchArgument)]
    assert arguments == ['namespace', 'record', 'bag_dir', 'subscriber_reliability']
    assert len([e for e in entities if isinstance(e, Node)]) == 4
    recorders = [e for e in entities if isinstance(e, ExecuteProcess) and not isinstance(e, Node)]
    assert len(recorders) == 1
    assert isinstance(recorders[0].condition, IfCondition)
