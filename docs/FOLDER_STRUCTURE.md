# FOLDER_STRUCTURE.md

---

# JARVIS MARK 5

Official Folder Structure Documentation

Version : Mark 5

---

# Purpose

This document defines the responsibility of every folder inside the project.

Every folder has one responsibility.

No folder should perform responsibilities assigned to another folder.

---

# ROOT DIRECTORY

Contains:

* Main entry point
* Configuration
* Documentation
* Dependency files

Examples

* main.py
* requirements.txt
* package.json
* jarvis_config.json

Root should remain clean.

---

# brain/

## Purpose

Artificial Intelligence Layer

The brain is responsible for reasoning.

It understands the user.

It decides what should happen.

It never executes system commands.

---

## Responsibilities

✓ LLM Communication

✓ Decision Making

✓ Context Understanding

✓ Intent Reasoning

✓ Conversation Logic

✓ Response Planning

---

## Must Never

❌ Shutdown PC

❌ Open Browser

❌ Click Mouse

❌ Execute Automation

❌ Play Music

---

# core/

## Purpose

Operating System Layer

Core connects all modules.

It contains infrastructure used by the entire project.

---

## Responsibilities

✓ Kernel

✓ Routing

✓ Startup

✓ Environment

✓ Personality

✓ Context

✓ Shared Components

✓ System Initialization

---

## Must Never

❌ Become another Brain

❌ Contain duplicated code

---

# memory/

## Purpose

Memory Layer

Stores information.

Retrieves information.

Ranks memories.

Maintains user profile.

---

## Responsibilities

✓ Long Term Memory

✓ Short Term Memory

✓ User Profile

✓ Memory Ranking

✓ Memory Search

---

## Must Never

❌ Generate responses

❌ Perform reasoning

❌ Execute automation

---

# voice/

## Purpose

Audio Layer

Everything related to listening and speaking belongs here.

---

## Responsibilities

✓ Speech Recognition

✓ Text To Speech

✓ Wake Word

✓ Interrupt

✓ Resume

✓ Audio Devices

---

## Must Never

❌ Think

❌ Decide

❌ Execute browser commands

---

# automation/

## Purpose

Execution Layer

Responsible for interacting with Windows and applications.

---

## Responsibilities

✓ Browser

✓ PC Control

✓ Spotify

✓ Mouse

✓ Keyboard

✓ Explorer

✓ Windows APIs

---

## Must Never

❌ Use LLM

❌ Perform reasoning

❌ Store memory

---

# vision/

## Purpose

Computer Vision Layer

Handles visual understanding.

---

## Responsibilities

✓ Camera

✓ OCR

✓ Screenshot Analysis

✓ Face Recognition

✓ Gesture Recognition

---

## Future Expansion

Screen AI

Object Detection

Scene Understanding

---

# agents/

## Purpose

Autonomous Agents

High-level planning and long-running tasks.

---

## Responsibilities

✓ Planning

✓ Scheduling

✓ Task Queue

✓ Goal Management

✓ Mission Management

---

## Future

Self Planning

Autonomous Execution

Agent Collaboration

---

# hud/

## Purpose

Graphical Interface

Shows system status.

Visualizes JARVIS.

---

## Responsibilities

✓ Electron HUD

✓ Animations

✓ Widgets

✓ Status Display

✓ Visual Feedback

---

## Must Never

❌ Think

❌ Execute commands

---

# utils/

## Purpose

Shared Utilities

Reusable helper functions.

---

## Responsibilities

✓ Logger

✓ Config

✓ Downloader

✓ Helpers

✓ Common Utilities

---

## Must Never

Contain business logic.

---

# docs/

## Purpose

Project Documentation

This folder is the single source of truth.

Every AI assistant must read documentation before modifying code.

---

Contains

PROJECT_ARCHITECTURE.md

FOLDER_STRUCTURE.md

CODING_RULES.md

CURRENT_STATUS.md

ROADMAP.md

API_REFERENCE.md

CHANGELOG.md

TASKS.md

AI_DEVELOPER_GUIDE.md

---

# Communication Rules

The communication path between folders is strictly controlled.

```text
User

↓

voice

↓

core.kernel

↓

brain

↓

memory

↓

intent

↓

automation

↓

voice

↓

User
```

Only Kernel coordinates modules.

---

# Dependency Rules

Brain

↓

Memory

↓

Context

↓

Intent

↓

Automation

Never the opposite.

Automation must never call Brain.

Memory must never call Automation.

Voice must never call Brain directly.

Kernel coordinates everything.

---

# Golden Rule

Every folder must have exactly one responsibility.

If a feature requires multiple responsibilities, split it into multiple modules instead of expanding an existing one.

---

End of Folder Structure Documentation.
