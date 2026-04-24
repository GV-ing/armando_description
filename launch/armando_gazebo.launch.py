from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, SetEnvironmentVariable
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
    pkg_share = get_package_share_directory('armando_description')
    # Percorso del file URDF di assemblaggio
    urdf_path = os.path.join(pkg_description_path, "urdf", "arm.urdf.xacro")
    default_world_path = os.path.join(pkg_description_path, "worlds", "armando_workbench.sdf")
    
    # Used to enable Gazebo simulation time
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
    )

    # Include worlds directory in GZ_SIM_RESOURCE_PATH
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.join(pkg_share, 'worlds') + ':' + os.path.join(pkg_share, 'models') + ':' + os.path.dirname(pkg_share) 
    )


    gz_gui_config_path = SetEnvironmentVariable(
            name='GZ_GUI_CONFIG_PATH',
            value=os.path.join(pkg_share, 'conf', 'gazebo.config')
        )

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


    # Bridge ROS <-> Gazebo unificato (camera e pose)
    bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/camera@sensor_msgs/msg/Image@gz.msgs.Image',
            '/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
            '/world/armando_workbench/dynamic_pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '--ros-args',
            '-r', '/camera:=/camera/image_raw',
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


    return LaunchDescription([
        declare_use_sim_time,
        gz_resource_path,
        gz_gui_config_path,
        robot_state_publisher_node,
        gui_arg,
        world_arg,
        gazebo_launch,
        spawn_robot_node,
        load_joint_state_broadcaster,
        load_joint_trajectory_controller,
        load_position_controller,
        bridge_node,
    ])

