# JSON Reference Guide

## Outline

1. [Overview](#overview)
2. [General Structure](#general-structure)
3. [Field Definitions](#field-definitions)
   - [section](#section)
   - [type](#type)
   - [embodiment](#embodiment)
4. [Verbal Block](#verbal-block)
5. [Nonverbal Block](#nonverbal-block)
6. [Summary Block](#summary-block)
7. [Child Behavior](#child-behavior)

This document defines the structure, fields, and allowed values for all study content used in the BST Study Interaction Framework.

All experimental behavior (tutorial, instruction, modeling, and DTT rehearsal) is fully data-driven through JSON files in the `data/` directory.

> **Note**: Some parameters are not used in the active version but left in for future improvements.

---

# Overview

Each JSON entry represents a single interaction step or trial and typically includes:

* Metadata (section, type, embodiment)
* Verbal behavior (speech output)
* Nonverbal behavior (gesture, gaze, facial expression, etc.)
* Child behavior (modeling condition)
* Summary fields

The system reads these files at runtime and converts them into robot behavior packets.

> **Note**: Some paramters are only used in certain phases currently but available across the entire system.

---

# General Structure

A typical entry follows this pattern:

```json
{
  "section": "string",
  "type": "content | knowledge_check",
  "embodiment": "trainer | kid",

  "verbal": { ... },
  "nonverbals": [ ... ]
}
```

---

# Field Definitions

## section

* Type: string
* Description: Identifies study phase or block that is currently being completed
* Examples:

  * `"intro"`
  * `"instruction_intro"`
  * `"modeling"`
  * `"trial_1"`

---

## type

* Type: string
* Allowed values:
  * `content`
  * `knowledge_check`
  * `led_demo or interaction` (tutorial only)  
* Description: Defines how the entry is executed in the study flow

---

## embodiment

* Type: string
* Allowed values:

  * `trainer`
  * `kid`
* Description:
  Defines which agent is active:

  * `trainer` → instructor robot behavior
  * `kid` → simulated learner response (modeling condition)

---

# Verbal Block

Defines speech output for the robot.

```json
"verbal": {
  "text": "Hello and welcome!",
  "style": "instructional",
  "volume": 60,
  "audio": null,
  "interrupt": false
}
```

## Fields

> **Note**: Default output parameters for these values can be altered in `expression_module/expression_module.py`

* **text** (string): Spoken content
* **style** (string): Speech style (e.g., instructional, conversational)
* **volume** (0–100): Speech volume
* **audio** (optional string): Path to audio file
* **interrupt** (boolean): Whether user speech can interrupt robot

---

# Nonverbal Block

Defines robot gestures, gaze, facial expressions, and other behaviors.

```json
"nonverbals": [
  {
    "channel": "face",
    "action": "Happy",
    "intensity": 1.0,
    "duration": 1.0,
    "timing": "during"
  }
]
```

## Channels

* face
* head
* gaze
* led

---

## Common Fields

* **channel**: modality of behavior (face expression, head gesture, gaze attention, LED control)
* **action**: specific behavior (e.g., Nod, Happy, LookUser)
* **intensity**: value of intensity varies (typically 1-5 or so)
* **duration**: duration in seconds (optional)
* **repeats**: number of repetitions (optional)
* **timing**: timing semantics

---

## Timing Semantics

* **before** → executes prior to speech
* **during** → executes while speech is active
* **after** → executes after speech completes

---

## Summary Block

Used in instruction and modeling phases to reinforce learning. Only applicable if the user pauses and asks for a summary.

```json
"summary": {
  "enabled": true,
  "text": "This section teaches the basic structure of BST interactions."
}
```

---

# Child Behavior

Used when simulating a learner response during modeling. An example of the verbal and nonverbal sections put together is as follows:

```json
"child_behavior": 
{
    "embodiment": "kid",

    "verbal": {
        "text": "I want to work for the ball!",
        "style": "instructional",
        "volume": 60,
        "audio": null,
        "interrupt": false
    },

    "nonverbals": [
      {
        "channel": "face",
        "action": "Happy",
        "intensity": 1.0,
        "duration": 1.0,
        "timing": "during"
      },
      {
        "channel": "head",
        "action": "Nod",
        "intensity": 0.5,
        "duration": 1.0,
        "repeats": 1,
        "timing": "during"
      },
      {
        "channel": "gaze",
        "action": "user",
        "timing": "during"
      }
    ]
}
```

# SD (Stimulus Discriminative) Configuration
Defines characteristics of the SD trial.

```json
"sd": "What do you want to work for?",
"sd_type": "Manding",
"correctness": "Correct",
"challenge": null,
"pb_response_type": null,
"action": null,
"object": null,
"emotion": "",
```

The `sd` field is the primary behavioral trigger used by the SD recognizer.

It MUST exactly match the spoken stimulus presented to the participant.

This field is NOT optional in practice and is used for:
- Speech recognition matching
- State transitions in DTT logic
- Correct/incorrect response evaluation
- Step progression in interaction flow

> **Critical**: The SD recognizer performs semantic matching against this field.
> Small changes in wording may break recognition accuracy.

## SD Fields

### Required

- **sd** (string)
  - The exact stimulus presented to the participant
  - Must match spoken prompt or be semantically equivalent
  - Used directly by SD recognizer for classification

### Optional (used in DTT logic only)

- **sd_type** (string)
  - Category of stimulus (e.g., Manding, Reception)
  - Used for analytics and grouping only

- **correctness** (string)
  - Expected response classification (Correct / Incorrect)
  - Used for reinforcement logic

### Future / Experimental Fields

- **challenge**
- **pb_response_type**
- **action**
- **object**
- **emotion**

---

# Valid Value Reference

## Styles

* instructional
* conversational

## Embodiments

* trainer
* kid

## Timing

* before
* during
* after

## Nonverbal Channels

* face
* head
* gaze
* led

---

# Common Mistakes

### ❌ Missing required fields

Always include:

* section
* type
* embodiment

---

### ❌ Invalid timing values

Only use:

* before
* during
* after

---

### ❌ Hardcoding behavior in Python

All robot behavior should be defined in JSON, not logic files.

---

### ❌ Inconsistent structure

Keep formatting consistent across all data files in `data/`.

---

# Extending the JSON Schema

The framework is designed to support new parameters and behavior types as research needs evolve.

When adding a new parameter:

1. Add the parameter to the appropriate JSON structure
- Define the new field within the relevant JSON block (e.g., verbal, nonverbal, SD configuration, child behavior).
- Provide sensible default values when possible.
2. Pass the parameter through the Expression Module
- Update expression_module/expression_module.py so the new parameter is included in the generated behavior packet.
- All parameters should be preserved and forwarded through the packet structure, even if they are not currently used by the active robot embodiment.
3. Update Agent Layer Translation (if needed)
- If the parameter affects robot behavior, add handling in: `agent_layer/Furhat/Lib/furhat_data_translate.py`
- Other embodiment-specific translators as applicable.
Not every parameter requires execution logic, but all parameters should be capable of passing through the system.
4. Implement Execution Logic (if needed)
- If the parameter changes robot behavior, add support in the relevant execution layer.
- Examples:
  - New gesture types
  - LED behaviors
  - Voice parameters
  - Attention targets

Recommended Data Flow
JSON Content -> Expression Module -> Behavior Packet -> Agent Layer Translation -> Robot Execution 

> **Best Practice:** New parameters should be introduced in a way that preserves backward compatibility with existing JSON files whenever possible.

---

# Best Practices

* Keep entries small and modular
* Prefer reusable behavior patterns
* Use consistent naming for SDs and sections
* Test JSON changes before running full study
* Use `trainer` vs `kid` explicitly for clarity

---

# Example Minimal Entry

```json
{
  "section": "intro",
  "type": "content",
  "embodiment": "trainer",
  "verbal": {
    "text": "Welcome to the study!"
  },
  "nonverbals": []
}
```

---

# Notes

This schema is designed to support:

* Behavioral Skills Training (BST)
* Discrete Trial Training (DTT)
* Instructional modeling and feedback
* Modular robot behavior execution

# Questions
If there are any bugs or issues found, please open an issue ticket here:

https://github.com/Intelligent-Robotics-Lab/bst-study/issues

For system-level architecture, reference:

* `docs/ARCHITECTURE.md` (coming soon)
* [Contributions Guide](CONTRIBUTING.md)