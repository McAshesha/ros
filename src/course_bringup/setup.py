from glob import glob

from setuptools import find_packages, setup

package_name = 'course_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='McAshesha',
    maintainer_email='mcashesha@mail.ru',
    description='Namespaced patrol launch, pose relay and QoS subscriber (PR05).',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'pose_relay = course_bringup.pose_relay:main',
            'pose_subscriber = course_bringup.pose_subscriber:main',
        ],
    },
)
