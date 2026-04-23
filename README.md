# MQ-to-Dify Essay Correction Bridge

A compatibility and integration project that maps MQ-based essay-correction data into a Dify workflow. The focus is on field mapping, migration safety, interoperability, and validation of the end-to-end bridge.

## What this project does

- Parses MQ-style essay correction payloads
- Maps source fields into Dify workflow inputs
- Validates field integrity and response compatibility
- Provides tests and notes for migration and integration scenarios

## Why it matters

This repository shows system-integration work rather than isolated feature work. It is useful as evidence of migration capability, compatibility reasoning, and workflow bridging.

## Main assets

- `FINAL_SUMMARY.md`: final validation summary
- `N8N_INTEGRATION.md`: integration notes
- `test_mq_to_dify.py`: end-to-end mapping test
- `test_dify_*.py`: focused validation scripts
- `check_syntax.py`: basic validation helper

## Key capabilities

- MQ to workflow integration
- Field-mapping validation
- Compatibility-focused design
- Workflow migration support

## Notes

This public repository is a cleaned release version. Local response dumps and sensitive runtime payloads were excluded.
