# channels/demo_channel.py Scenarios

## Scenario A: Default Week 14 Demo

- Command: `py agent.py`
- Expected result:
  - Loads `project/scenarios/demo_scenarios.json`
  - Returns 3 realistic construction scenarios

## Scenario B: Custom Scenario File

- Command:
  - `py agent.py --scenario-file path\\to\\custom.json`
- Expected result:
  - Demo channel loads custom scenario set

## Scenario C: Missing Scenario File

- Input:
  - Invalid path
- Expected result:
  - Clear runtime error about missing scenario file
