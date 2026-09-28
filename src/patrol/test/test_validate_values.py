import math

from patrol.patrol import validate_values
import pytest


def test_defaults_are_valid():
    assert validate_values(10.0, 0.5, 0.3) == (True, '')


def test_rate_change_10_to_5_is_valid():
    ok, reason = validate_values(5.0, 0.5, 0.3)
    assert ok
    assert reason == ''


@pytest.mark.parametrize('publish_hz', [0.0, -1.0, math.nan, math.inf, 0.5, 30.5])
def test_bad_publish_hz_is_rejected(publish_hz):
    ok, reason = validate_values(publish_hz, 0.5, 0.3)
    assert not ok
    assert reason.startswith('publish_hz')


@pytest.mark.parametrize('publish_hz', [1.0, 30.0])
def test_publish_hz_bounds_are_valid(publish_hz):
    assert validate_values(publish_hz, 0.5, 0.3)[0]


@pytest.mark.parametrize('linear_speed', [-0.1, 1.1, math.nan])
def test_bad_linear_speed_is_rejected(linear_speed):
    ok, reason = validate_values(10.0, linear_speed, 0.3)
    assert not ok
    assert reason.startswith('linear_speed')


@pytest.mark.parametrize('turn_rate', [-1.1, 1.1, -math.inf])
def test_bad_turn_rate_is_rejected(turn_rate):
    ok, reason = validate_values(10.0, 0.5, turn_rate)
    assert not ok
    assert reason.startswith('turn_rate')


def test_non_number_is_rejected():
    assert not validate_values('10', 0.5, 0.3)[0]
    assert not validate_values(10.0, True, 0.3)[0]
