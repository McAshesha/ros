import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import pytest

MODEL = Path(__file__).resolve().parents[1] / 'urdf/vehicle.urdf.xacro'


def expand(**parameters):
    command = ['xacro', str(MODEL)] + [f'{k}:={v}' for k, v in parameters.items()]
    return ET.fromstring(subprocess.check_output(command, text=True))


def joint_for(model, child):
    return next(j for j in model.findall('joint') if j.find('child').get('link') == child)


def numbers(element, attribute):
    return tuple(float(v) for v in element.get(attribute).split())


def test_tree_is_connected_and_acyclic():
    model = expand()
    links = {link.get('name') for link in model.findall('link')}
    parents = {}
    for joint in model.findall('joint'):
        parent = joint.find('parent').get('link')
        child = joint.find('child').get('link')
        assert parent in links and child in links
        assert child not in parents
        parents[child] = parent
    assert links - parents.keys() == {'base_link'}
    for link in links:
        seen = set()
        while link in parents:
            assert link not in seen
            seen.add(link)
            link = parents[link]
        assert link == 'base_link'


@pytest.mark.parametrize('sensor', ['camera_link', 'lidar_link', 'imu_link'])
def test_sensor_parent_and_offset(sensor):
    joint = joint_for(expand(), sensor)
    assert joint.get('type') == 'fixed'
    assert joint.find('parent').get('link') == 'base_link'
    assert numbers(joint.find('origin'), 'xyz') == pytest.approx((0.28, 0, 0.38))


@pytest.mark.parametrize('wheelbase, track, radius', [(0.8, 0.62, 0.12), (1.0, 0.8, 0.15)])
def test_geometry_is_parameterized(wheelbase, track, radius):
    model = expand(wheelbase=wheelbase, track=track, wheel_radius=radius)
    for name, x, y in [
        ('front_left_knuckle_link', wheelbase / 2, track / 2),
        ('front_right_knuckle_link', wheelbase / 2, -track / 2),
        ('rear_left_wheel_link', -wheelbase / 2, track / 2),
        ('rear_right_wheel_link', -wheelbase / 2, -track / 2),
    ]:
        joint = joint_for(model, name)
        assert numbers(joint.find('origin'), 'xyz') == pytest.approx((x, y, 0))
    for name in ['front_left', 'front_right', 'rear_left', 'rear_right']:
        link = model.find(f"link[@name='{name}_wheel_link']")
        for kind in ['visual', 'collision']:
            cylinder = link.find(f'{kind}/geometry/cylinder')
            assert float(cylinder.get('radius')) == pytest.approx(radius)
            assert float(cylinder.get('length')) == 0.07
        inertia_y = float(link.find('inertial/inertia').get('iyy'))
        assert inertia_y == pytest.approx(0.8 * radius**2 / 2)
    for name in ['front_left', 'front_right']:
        assert numbers(joint_for(model, f'{name}_wheel_link').find('origin'), 'xyz') == (0, 0, 0)


def test_geometry_mass_and_inertia_are_physical():
    model = expand()
    total_mass = 0
    for link in model.findall('link'):
        mass = float(link.find('inertial/mass').get('value'))
        assert math.isfinite(mass) and mass > 0
        total_mass += mass
        inertia = link.find('inertial/inertia')
        diagonal = [float(inertia.get(k)) for k in ['ixx', 'iyy', 'izz']]
        assert all(math.isfinite(v) and v > 0 for v in diagonal)
        assert max(diagonal) <= sum(diagonal) - max(diagonal)
        assert all(float(inertia.get(k)) == 0 for k in ['ixy', 'ixz', 'iyz'])
        for kind in ['visual', 'collision']:
            geometry = link.find(f'{kind}/geometry')
            box = geometry.find('box')
            values = numbers(box, 'size') if box is not None else (
                float(geometry.find('cylinder').get('radius')),
                float(geometry.find('cylinder').get('length')),
            )
            assert all(math.isfinite(v) and v > 0 for v in values)
    assert total_mass == pytest.approx(15.7)
    base = model.find("link[@name='base_link']")
    assert numbers(base.find('visual/geometry/box'), 'size') == (1.05, 0.52, 0.22)
    assert numbers(base.find('collision/origin'), 'xyz') == (0, 0, 0.12)


def test_check_urdf_accepts_model(tmp_path):
    model = tmp_path / 'vehicle.urdf'
    model.write_text(subprocess.check_output(['xacro', str(MODEL)], text=True))
    result = subprocess.run(['check_urdf', str(model)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
