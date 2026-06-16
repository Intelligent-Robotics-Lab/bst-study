# BST Study Interaction Framework
Study 1: Understanding perception of the robot's challenging and supportive behaviors through BST.

## Overview
This project is a robot interaction frameowrk for a behavioral skills training (BST) study. It combines perception, instructional content, and robot execution to run tutorial, instruction, modeling, and rehearsal phases on a Furhat robot while reacting to user inputs.

## Project Goals

## Project Structure

bst-study/
├─ main.py
├─ README.md
├─ requirements.txt
├─ webpage.py
├─ agent_layer/                             # Agent-specific beahvior translation
│  ├─ agent_layer.py
│  └─ Furhat/
│     ├─ Exe/
|       └─ furhat_execute.py
│     └─ Lib/
|       ├─ furhat_behavior_components.py
|       ├─ furhat_behavior_library.py
|       ├─ furhat_data_translate.py
|       └─ furhat_manager.py
├─ expression_module/                       # Packet builder for root behaviors
│  └─ expression_module.py
├─ logic/                                   # Interaction flows and study modules
│  ├─ base_interaction.py
|  ├─ bst.py
│  ├─ dtt.py
│  ├─ feedback.py
│  ├─ instruction.py
│  ├─ modeling.py
│  ├─ monitor.py
│  ├─ sd_recognizer.py
│  └─ tutorial.py
├─ perception/                              # ASR, gesture, and emotion input handling
│  ├─ perception_client.py
│  ├─ perception_instruction.py
│  ├─ sample_interaction.py
│  └─ perception_requirements.txt
├─ data/                                    # Step definition and study content
│  ├─ expression_testing.json
│  ├─ hp_trial_data.json
│  ├─ instruction_data.json
│  ├─ modeling_data.json
│  ├─ monitor_state.json
│  ├─ trial_data.json
│  └─ tutorial_data.json
├─ sounds/
│  ├─ generate_scream.py
│  └─ *.wav
├─ test/
│  └─ *.py
├─ templates/
│  └─ index.html

## Architecture
- Perception
- Logic
- Expression module
- Agent layer

## Quick Start

## Installation

## Configuration

## How to Run

## Troubleshooting

## Contributing

## License


