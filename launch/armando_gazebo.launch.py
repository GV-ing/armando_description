from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.event_handlers import OnProcessExit
from ament_index_python.packages import get_package_share_directory
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    # Ottieni il percorso del pacchetto
    pkg_description_path = get_package_share_directory('armando_description')

    # Percorso del file URDF di assemblaggio
    urdf_path = os.path.join(pkg_description_path, "urdf", "arm.urdf.xacro")
    default_world_path = os.path.join(pkg_description_path, "worlds", "armando_workbench.sdf")

    # Argomento per avviare Gazebo con o senza GUI
    gui_arg = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Avvia Gazebo con GUI'
    )

    world_arg = DeclareLaunchArgument(
        name='world',
        default_value=default_world_path,
        description='Percorso del world SDF da caricare in Gazebo'
    )

    # Genera la descrizione del robot processando xacro
    robot_description_content = ParameterValue(
        Command([
            'xacro ', urdf_path,
            ' package_path:=', pkg_description_path
        ]),
        value_type=str
    )

    robot_description_param = {'robot_description': robot_description_content}

    # Nodo: robot_state_publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description_param],
    )

    # Launch di Gazebo Harmonic
    gazebo_launch = IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']),
        launch_arguments={
            #'gz_args': ['-r -v 4 empty.sdf'],
            'gz_args': ['-r -v 4 ', LaunchConfiguration('world')],
            'on_exit_shutdown': 'true'
        }.items(),
    )

    # Nodo: spawn del robot in Gazebo
    spawn_robot_node = Node(
        package='ros_gz_sim',
        executable='create',
        name='urdf_spawner',
        arguments=[
            '-topic', '/robot_description',
            '-entity', 'armando',
            '-x', '0.45',
            '-y', '0.0',
            '-z', '0.44',
            '-allow_renaming', 'true'
        ],
        output='screen',
    )

    # Spawner del joint state broadcaster
    spawn_joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    # Spawner del position controller (caricato ma non attivo)
    spawn_position_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['position_controller', '--controller-manager', '/controller_manager', '--inactive'],
    )

    # Spawner del joint trajectory controller
    spawn_joint_trajectory_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_trajectory_controller', '--controller-manager', '/controller_manager'],
    )

    # Spawner del gripper controller
    spawn_gripper_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['gripper_controller', '--controller-manager', '/controller_manager', '--inactive'],
    )

    # Bridge ROS <-> Gazebo per la camera
    bridge_camera_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/camera@sensor_msgs/msg/Image@gz.msgs.Image',
            '/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
            '--ros-args',
            '-r', '/camera:=/camera/image_raw',
        ],
        output='screen',
    )

    # Bridge ROS <-> Gazebo per le pose degli ostacoli dinamici
    # Usa il topic dynamic_pose/info che contiene tutte le pose dinamiche
    bridge_poses_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/world/armando_workbench/dynamic_pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        ],
        output='screen',
    )

    # Event handler: avvia i controller dopo lo spawn del robot
    load_joint_state_broadcaster = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot_node,
            on_exit=[spawn_joint_state_broadcaster],
        )
    )

    load_joint_trajectory_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_joint_state_broadcaster,
            on_exit=[spawn_joint_trajectory_controller],
        )
    )

    # Carica il position controller in stato inactive per permettere switch a runtime
    load_position_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_joint_trajectory_controller,
            on_exit=[spawn_position_controller],
        )
    )

    load_gripper_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_position_controller,
            on_exit=[spawn_gripper_controller],
        )
    )

    return LaunchDescription([
        gui_arg,
        world_arg,
        robot_state_publisher_node,
        gazebo_launch,
        spawn_robot_node,
        load_joint_state_broadcaster,
        load_joint_trajectory_controller,
        load_position_controller,
        load_gripper_controller,
        bridge_camera_node,
        bridge_poses_node,
    ])

