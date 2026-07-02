# API_REFERENCE.md

## Brain

Class

Brain()

Methods

process_query(query)

Parameters

query : str

Returns

str

Description

Processes user query and returns intelligent response.

------------------------------------

## Kernel

Class

Kernel()

Methods

initialize()

Starts all project modules.

------------------------------------

process_query(query)

Routes request through complete system.

------------------------------------

get_greeting()

Returns startup greeting.

------------------------------------

## Voice

speak(text)

Parameters

text : str

Returns

None

------------------------------------

stop_speaking()

Stops current playback.

------------------------------------

resume_speech()

Resumes interrupted speech.

------------------------------------

is_speaking()

Returns bool

------------------------------------

## Memory

save()

load()

remember()

recall()

------------------------------------

## Browser

open_url()

search_google()

close_tab()

new_tab()

------------------------------------

## PC Control

shutdown()

restart()

sleep()

lock()

volume_up()

volume_down()

mute()

------------------------------------

## Environment

get_cpu()

get_ram()

get_gpu()

get_battery()

------------------------------------

## Context

get_context()

update_context()

clear_context()

------------------------------------

## Intent Engine

classify(query)

Returns

Intent Object

------------------------------------

## Tool Manager

execute_intent(intent)

Returns

Execution Result

------------------------------------

## HUD

update_hud()

show_notification()

update_widget()

------------------------------------

Future APIs

Vision

OCR

Face Recognition

Gesture Recognition

Planning Agent

Mission Manager

Scheduler

Knowledge Graph