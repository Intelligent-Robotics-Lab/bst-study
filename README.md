# BST Study Interaction Framework
Study 1: Understanding perception of the robot's challenging and supportive behaviors through BST.

## Overview
This project is a robot interaction framework for a behavioral skills training (BST) study. It combines perception, instructional content, and robot execution to run tutorial, instruction, modeling, and rehearsal phases on a Furhat social robot while reacting to participant responses.

### BST Study Phases
1. **Tutorial**
   - Introduces participants to the interaction model and robot behavior.
2. **Instruction**
   - Teaches target BST concepts through structured robot guidance.
3. **Modeling**
   - Demonstrates desired intervention and interaction behaviors while explaining proper responding over 5 SD types.
4. **Rehearsal**
   - Allows participant to practice 6 instructions with feedback and response evaluation.

## Project Goals
This system is designed to:
- Deliver structured BST interactions through a social robot.
- Monitor participant state and responses via perception input.
- Support experimental variation of robot behaviors.
- Separate perception, logic, expression, and agent execution into modular layers.

## Repo Structure

```text
bst-study/
├─ main.py                       # Entry point for the BST application
├─ README.md                     # Project overview and usage notes
├─ requirements.txt              # Python dependency list
├─ webpage.py                    # User-facing dashboard for study
├─ agent_layer/                  # Robot-specific command translation
│  ├─ agent_layer.py             # Base agent interface and packet adapter
│  └─ Furhat/
│     ├─ Exe/                    # Furhat runtime entrypoint
│     │  └─ furhat_execute.py
│     └─ Lib/                    # Furhat utility modules
│        ├─ furhat_behavior_components.py
│        ├─ furhat_behavior_library.py
│        ├─ furhat_data_translate.py
│        └─ furhat_manager.py
├─ expression_module/            # Builds generic robot behavior packets
│  └─ expression_module.py
├─ logic/                        # Study phase controllers and interaction flows
│  ├─ base_interaction.py
│  ├─ bst.py
│  ├─ dtt.py
│  ├─ feedback.py
│  ├─ instruction.py
│  ├─ modeling.py
│  ├─ monitor.py
│  ├─ sd_recognizer.py
│  └─ tutorial.py
├─ perception/                   # Input handling for ASR, gesture, and emotion
│  ├─ perception_client.py
│  ├─ sample_interaction.py
│  └─ perception_requirements.txt
├─ data/                         # JSON content for study steps, trials, and monitor state
│  ├─ expression_testing.json
│  ├─ hp_trial_data.json
│  ├─ instruction_data.json
│  ├─ modeling_data.json
│  ├─ monitor_state.json
│  ├─ trial_data.json
│  └─ tutorial_data.json
├─ docs/                         # Documentation resources 
│  └─ CONTRIBUTING.md
├─ sounds/                       # Audio utilities and generated sound files
│  ├─ generate_scream.py
│  └─ *.wav
├─ test/                         # Unit and integration tests
│  └─ *.py
├─ templates/                    # Static web page templates
│  └─ index.html
```

## Architecture
The framework follows a layered architecture:

Perception → Logic → Expression Module → Agent Layer

(Placeholder for system architecture diagram)

1. **Perception**
   - Receives live inputs from the user, including speech recognition, gesture detection, and emotion inference.
   - Routes events into the interaction pipeline and triggers robot responses when required.
2. **Logic**
   - Controls the study progression through tutorial, instruction, modeling, and DTT phases.
   - Uses `BaseInteraction` and its subclasses to manage step execution, navigation, and knowledge checks.
3. **Expression module**
   - Builds embodiment-independent behavior packets from step definitions.
   - Defines speech text, nonverbal events, and other robot cues in a generic format.
4. **Agent layer**
   - Translates generic packets into robot-specific commands.
   - For Furhat, it converts behaviors into the API calls needed to speak, gesture, set LEDs, control attention, etc.

## Quick Start
Before launching, ensure:
- The Furhat is powered on and connected to the same network as your local machine.
- Furhat IPs are configured correctly.
- The perception dashboard shows incoming events: http://141.210.88.210:8000/debug/live

1. Create and activate a virtual environment:
```powershell
python -m venv .\venv
.\venv\Scripts\activate
```
2. Install dependencies:
```powershell
pip install -r requirements.txt
```
3. Start the study application:
```powershell
python main.py
```

The system will connect to the perception service, initialize the Furhat robot, load study content, and begin the BST interaction sequence.

## Installation
### Requirements
- Furhat robot with Realtime API access
- Running perception backend
- Network connectivity between all devices

### Setup
1. Create and activate a virtual environment:
```powershell
python -m venv .\venv
.\venv\Scripts\activate
```

2. Install the required dependencies:
```powershell
pip install -r requirements.txt
```

> Note: Addition perception dependencies may be required via: perception/perception_requirements.txt

## External Dependencies
The framework relies on several external systems:

- Furhat SDK and Realtime API services
- Perception backend service
- Websocket communication
- Audio and video input devices for speech and emotion recognition

Ensure compatibility and access to these features otherwise the system will not function as intended.

> Note: This framework can be built upon to support various agent embodiments and adjusted based on external dependency availability.

## Configuration
### Study Content
Study content is defined in the JSON files located in data/.
Common files include:
- tutorial_data.json
- instruction_data.json
- modeling_data.json
- trial_data.json
- hp_trial_data.json

For examples of supported parameters and valid values, refer to the various existing JSON files to compile full parameter lists.

### Agent Configuration
Robot settings are configured through
- logic/bst.py
- agent_layer/Furhat/Lib/furhat_manager.py
- agent_layer/Furhat/Lib/furhat_data_translate.py

Notable configurable parameters include robot IP address and agent embodiment.

### Perception Configuration
Perception settings are configured through:
- perception/perception_client.py
- perception/sample_interaction.py

A live perception dashboard is available for monitoring perception events: http://141.210.88.210:8000/debug/live

Ensure proper setup of server IP addresses, ports, and event handling configuration.
The framework expects perception events such as
- asr_update
- gesture_update
- emotion_update

## How to Run
### Running the Full Study
Start the application from the repository root:
```powershell
python main.py
```

This launches the full study sequence, which executes:
1. Tutorial
2. Instruction
3. Modeling
4. DTT

### Running Individual Modules
To run a single phase manually, instantiate the appropriate class from logic/ and call its execute() method from a Python shell or script. 

For example:
```python
from logic.tutorial import Tutorial

Tutorial(agent="Furhat").execute()
```
For a simpler version you can simply comment out the undesired modules in the bst.py file.

### Expected Runtime Flow
- The system starts in tutorial mode to orient the participant.
- It then transitions to instruction mode, delivering lesson content.
- Modeling mode demonstrates behavior and guides the participant.
- Rehearsal / DTT mode tests participant responses and provides feedback.

## Troubleshooting

For bugs, feature requests, or questions, please open an issue here:

https://github.com/Intelligent-Robotics-Lab/bst-study/issues

---

### Common Issues:

### Robot Not Responding
- Verify the Furhat robot is powered on and connected to the same network.
- Confirm the `AGENT_TYPE` is correct and that Furhat services are reachable via the web interface.
- Check the robot IP address and the Furhat connection logs.
- Make sure the agent layer is receiving packets from the expression module.

### Speech Recognition Not Working
- Confirm the perception server is running and reachable at http://141.210.88.210:8000/debug/live
- Check that `perception/perception_client.py` points to the correct host and port.
- Verify ASR events are emitted and forwarded to `SampleInteractionAgent`.

### Packet Executes But Robot Does Not Move
- Check the agent type wiring in `logic/base_interaction.py`.
- Confirm that `expression_module/expression_module.py` builds packets correctly.
- Verify Furhat translation in `agent_layer/Furhat/Lib/furhat_data_translate.py`.

## Additional Documentation

- [Contributing Guide](docs/CONTRIBUTING.md)
- Architecture Guide (Coming Soon)
- JSON Reference (Coming Soon)

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines, branching strategy, coding standards, and pull request expectations.

## License
Placeholder