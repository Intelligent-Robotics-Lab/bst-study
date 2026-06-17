# JSON Reference Guide

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

# Child Behavior (Modeling and Rehearsal Only)

Used when simulating a learner response during modeling. Example can be seen below:

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

For system-level architecture, see:

* `docs/ARCHITECTURE.md` (coming soon)
* [CONTRIBUTING.md](CONTRIBUTING.md)