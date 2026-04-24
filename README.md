# armando_description

Package ROS 2 contenente la descrizione fisica e visuale del braccio robotico Armando, sviluppato per scopi didattici e di simulazione.

## 📚 Contenuti

- **urdf/**: file Xacro che descrivono il braccio robotico, inclusi link, giunti e sensori
- **meshes/**: geometrie 3D e asset per la simulazione
- **worlds/**: mondi SDF utilizzati per la simulazione (workbench)
- **launch/**: file di lancio per avviare la simulazione e la visualizzazione
- **config/**: file di configurazione per RViz e parametri del braccio
- **CMakeLists.txt** e **package.xml**: configurazione del pacchetto ROS 2

## 🚀 Launch Files

Il pacchetto `armando_description` include due file di lancio principali:

### armando_gazebo.launch.py
Gestisce l'ambiente di simulazione fisica in Gazebo Harmonic. Simula la dinamica del braccio robotico, i sensori e carica il mondo virtuale (`.sdf`).

```bash
ros2 launch armando_description armando_gazebo.launch.py
```

### armando_rviz.launch.py
Avvia l'interfaccia di visualizzazione in RViz2. Si iscrive ai topic runtime come TF transforms e dati della camera, e li visualizza in una vista 3D.

```bash
ros2 launch armando_description armando_rviz.launch.py

```bash
ros2 launch armando_description armando_rviz.launch.py
```

## 📦 Installazione

Clonare questo repository nella cartella `src` del proprio workspace ROS 2:

```bash
cd ~/ros2_ws/src
git clone https://github.com/GV-ing/armando_description.git
cd ~/ros2_ws
colcon build --packages-select armando_description
source install/setup.bash
```

## 🎯 Utilizzo

Per lanciare la simulazione completa:

1. In un terminale, avviare Gazebo:
   ```bash
   ros2 launch armando_description armando_gazebo.launch.py
   ```

2. In un secondo terminale, avviare RViz:
   ```bash
   ros2 launch armando_description armando_rviz.launch.py
   ```

## 🛠️ Requisiti

- ROS 2 Humble
- Gazebo Harmonic
- RViz2
- xacro

## 📝 Note



