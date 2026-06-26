# Architecture Guide

This document describes the architecture of the BST Study Interaction Framework in detail. It explains each layer, the data model, the runtime flow, and the extension points so contributors can update the system safely.

## Outline

1. [Overview](#overview)
2. [Design principles](#design-principles)
3. [Architecture layers](#architecture-layers)
   - [Perception](#perception)
   - [Logic](#logic)
   - [Expression module](#expression-module)
   - [Agent layer](#agent-layer)
4. [Behavioral data model](#behavioral-data-model)
5. [Runtime data flow](#runtime-data-flow)
6. [Repository mapping](#repository-mapping)
7. [Extension points](#extension-points)
8. [Deployment and startup](#deployment-and-startup)
9. [Troubleshooting guide](#troubleshooting-guide)

---

## Overview

The BST Study Interaction Framework is a modular, data-driven system for running controlled robot interactions during a behavioral skills training study.

It separates:

- input acquisition from external sensors,
- study state and decision logic,
- generic behavior representation, and
- robot-specific execution.

This separation enables:

- reuse of study logic across embodiments,
- content changes via JSON instead of code,
- easier debugging by isolating faults to a single layer,
- and future expansion for new sensors, phases, or robots.

---

## Design principles

The architecture is guided by these principles:

- **Layered responsibilities**: each component has a defined role.
- **Data-driven design**: interaction content is authored in JSON.
- **Embodiment independence**: core logic and behavior packets are robot-agnostic.
- **Observable flow**: events and outputs should be inspectable at each stage.
- **Minimal coupling**: adding support for new hardware or phases should not require rewriting the full system.

---

## Architecture layers

### Perception

The perception layer ingests external inputs and converts them into the internal event model.

Primary responsibilities:

- Accept sensor and recognition events from the perception service.
- Parse raw input into structured events.
- Validate event payloads and required fields.
- Forward normalized events to the logic layer.
- Provide mocked input for offline or development testing.

Typical event types:

- `asr_update`
- `gesture_update`
- `emotion_update`
- operator commands or manual triggers

Key files:

- `perception/perception_client.py`
  - Handles event connection and incoming payload parsing.
  - Converts perception service messages into internal event structures.
- `perception/sample_interaction.py`
  - Simulates perception input for local testing.
  - Useful for validating logic without a live perception server.
- `perception/perception_requirements.txt`
  - Lists dependencies needed for perception-related services.

Why it matters:

The perception layer is the system�s input gateway. If it fails to normalize events consistently, the logic layer cannot apply the correct study rules.

### Logic

The logic layer is responsible for study flow, phase transitions, participant response evaluation, and high-level decision making.

Primary responsibilities:

- Manage study phases and transitions.
- Track trial state, participant progress, and session metadata.
- Interpret perception events in the current task context.
- Select the next behavior step or corrective action.
- Determine when to advance, repeat, or provide feedback.

Core modules:

- `logic/base_interaction.py`
  - Base class for phase controllers.
  - Contains generic utilities for state transitions, step execution, and content loading.
- `logic/bst.py`
  - Main BST study orchestrator.
  - Coordinates tutorial, instruction, modeling, rehearsal, and assessment phases.
- `logic/tutorial.py`
  - Tutorial phase behavior and introductory flow.
- `logic/instruction.py`
  - Instruction phase with knowledge checks and procedural explanation.
- `logic/modeling.py`
  - Modeling phase that simulates learner responses.
- `logic/dtt.py`
  - Discrete trial teaching phase with response validation.
- `logic/feedback.py`
  - Feedback generation and reinforcement decisions.
- `logic/monitor.py`
  - Tracks participant state and experimental monitoring data.
- `logic/sd_recognizer.py`
  - Stimulus discrimination recognition logic used across phases.

How it works:

1. A perception event arrives.
2. The current phase controller determines whether the event satisfies the current task conditions.
3. The controller updates internal state and trial history.
4. If a new action is required, the step is forwarded to the expression module.

Why it matters:

The logic layer implements the study rules. It is the decision-making core that determines how the system responds to participant behavior and progresses through the experiment.

### Expression module

The expression module converts study steps into a generic behavior packet that is independent of any robot implementation.

Primary responsibilities:

- Build a standard packet schema from JSON content and logic decisions.
- Normalize speech, gesture, gaze, and timing information.
- Combine verbal and nonverbal behavior definitions into a single output structure.
- Apply defaults and resolve missing or optional behavior fields.

Packet components:

- `verbal`
  - text, style, volume, audio file path, interrupt behavior
- `nonverbals`
  - gestures, facial expressions, gaze direction, LEDs, timing, duration
- `summary`
  - optional review or reinforcement text
- `child_behavior`
  - simulated learner response for modeling phases

Key files:

- `expression_module/expression_module.py`
  - Core packet generation and normalization logic.
  - Converts JSON content into the behavior packet schema.

Why it matters:

By keeping packet generation separate from robot execution, the same study interactions can be reused with different embodiments and eventually different robot platforms.

### Agent layer

The agent layer translates generic behavior packets into concrete commands for a robot platform.

Primary responsibilities:

- Accept generic behavior packets from the expression module.
- Validate packet contents against robot capabilities.
- Map packet fields to robot-specific APIs.
- Execute commands on the robot runtime.
- Manage connection and lifecycle state with the robot.

Key files:

- `agent_layer/agent_layer.py`
  - Central adapter interface for all embodiments.
  - Routes generic packets to the appropriate robot-specific backend.
- `agent_layer/Furhat/Exe/furhat_execute.py`
  - Executes commands on the Furhat runtime.
- `agent_layer/Furhat/Lib/furhat_behavior_components.py`
  - Defines Furhat-specific behavior primitives.
- `agent_layer/Furhat/Lib/furhat_behavior_library.py`
  - Provides reusable Furhat action sequences.
- `agent_layer/Furhat/Lib/furhat_data_translate.py`
  - Maps generic packet fields to Furhat command structures.
- `agent_layer/Furhat/Lib/furhat_manager.py`
  - Furhat lifecycle and connection management.

Why it matters:

The agent layer makes the system robot-aware. It is the bridge between the generic study behavior and the physical robot execution.

---

## Behavioral data model

The system is data-driven: study content, trials, and behavior definitions are stored in JSON files.

Primary data files:

- `data/tutorial_data.json`
- `data/instruction_data.json`
- `data/modeling_data.json`
- `data/trial_data.json`
- `data/hp_trial_data.json`
- `data/monitor_state.json`
- `data/expression_testing.json`

Common JSON fields:

- `section`
- `type`
- `embodiment`
- `verbal`
- `nonverbals`
- `summary`
- `child_behavior`

Field semantics:

- `section`: identifies the study phase or block.
- `type`: distinguishes content from knowledge checks and special interactions.
- `embodiment`: determines whether the trainer or simulated child speaks.
- `verbal`: speech details.
- `nonverbals`: gesture and expression details.
- `summary`: optional review text.
- `child_behavior`: simulated learner response content in modeling.

Why it matters:

This data model makes it easy to update the study script without code changes. New behaviors can be authored by editing JSON files and keeping the packet schema stable.

---

## Runtime data flow

The system operates as a repeating event-driven loop.

1. **Perception receives raw input**
   - Events come from the perception service or mock input.
2. **Perception normalizes the event**
   - Raw payloads are converted into the internal event format.
3. **Logic evaluates the event**
   - The current phase controller interprets the event within the study context.
4. **Logic selects the next action**
   - A new step, correction, or transition is chosen.
5. **Expression module builds a packet**
   - The selected step is turned into a generic behavior packet.
6. **Agent layer executes the packet**
   - The packet is translated and sent to the robot.
7. **The system waits for the next event or completion**
   - The loop repeats until the session ends.

This flow enables both scripted interactions and adaptive responses to participant behavior.

---

## Repository mapping

Directory responsibilities:

- `main.py`
  - Entry point and orchestrator.
  - Initializes perception, logic, expression, and agent subsystems.
- `webpage.py`
  - Dashboard for monitoring live sessions.
- `agent_layer/`
  - Robot-specific execution adapters.
- `expression_module/`
  - Behavior packet generation.
- `logic/`
  - Study phase controllers and decision logic.
- `perception/`
  - Input event ingestion and normalization.
- `data/`
  - Study content and trial definitions.
- `sounds/`
  - Audio utilities and sound assets.
- `test/`
  - Unit and integration tests.

---

## Extension points

### Add a new perception source

1. Implement a new client in `perception/`.
2. Normalize new event types to the existing internal schema.
3. Update logic event handling if new semantic events are needed.

### Add a new study phase

1. Add a phase controller in `logic/`.
2. Extend `logic/bst.py` or `logic/base_interaction.py` for phase transitions.
3. Add JSON content for the new phase.
4. Verify the expression module can translate new packet fields.

### Add a new robot embodiment

1. Add a new folder under `agent_layer/`.
2. Implement an adapter that consumes generic packets.
3. Translate packet fields into the new robot API.
4. Keep the existing expression schema stable.

### Extend JSON behavior fields

1. Update `docs/JSON_REFERENCE.md` with the new field definitions.
2. Update `expression_module/expression_module.py` to normalize the new fields.
3. Ensure the agent layer supports the resulting packet semantics.

---

## Deployment and startup

Expected environment:

- Python dependencies installed from `requirements.txt`
- Perception dependencies installed from `perception/perception_requirements.txt` (if needed)
- Furhat robot reachable on the same network
- Perception backend running and reachable
- `OPENAI_KEY` available in `.env` if AI-based feedback is enabled

Startup steps:

1. Create and activate a Python virtual environment.
2. Install dependencies.
3. Confirm Furhat and perception service connectivity.
4. Run the application:
   ```powershell
   python main.py
   ```
5. Monitor the session through the web dashboard.

---

## Troubleshooting guide

Troubleshooting is most effective when isolating the problem by layer.

### Perception issues

- Symptoms: no events, malformed input, stale or intermittent events.
- Check: perception backend connectivity, event schema, logs in `perception_client.py`.
- Fix: verify the perception endpoint and test with `perception/sample_interaction.py`.

### Logic issues

- Symptoms: incorrect phase transitions, repeated behavior, failure to progress.
- Check: state updates in `logic/base_interaction.py`, phase logic in `logic/*` controllers.
- Fix: trace the current controller state and event evaluation.

### Expression issues

- Symptoms: missing speech, wrong gesture timing, incomplete packet data.
- Check: packet construction in `expression_module/expression_module.py`.
- Fix: validate JSON field mappings and default values.

### Agent issues

- Symptoms: robot does not act, execution errors, unsupported commands.
- Check: robot session state, command translation in `agent_layer/Furhat/Lib`, Furhat logs.
- Fix: ensure the packet fields are supported by the robot embodiment and the runtime connection is healthy.

When in doubt, follow the path: perception ? logic ? expression ? agent.