# Economy V1 Progress

## Implemented Scope

- Added `app/economy` runtime domain with resource definitions, catalog loading, config repository, rebirth point settlement, and run resource stack helpers.
- Added `config/economy/resources.json` and `config/economy/settlement.json` as the current local source of truth for economy config.
- Added `resource_stacks` to `RunState` and `rebirth_points` to `PlayerProfile`.
- Connected rebirth flow to award rebirth points and reset run resource stacks when a new run is created.
- Connected event payload rewards to the unified economy compatibility layer so non-legacy resource keys can be written into `run.resource_stacks`.
- Added `required_materials` to realm config as a forward-compatible breakthrough requirement shape while keeping current breakthrough behavior limited to cultivation and spirit stones.

## Current Resource Set

- `spirit_stone`
- `basic_herb`
- `basic_ore`
- `basic_breakthrough_material`
- `rare_material`

## Rebirth Point Settlement

Current rebirth points are calculated from four weighted dimensions in `config/economy/settlement.json`:

- realm order index
- survived rounds
- rare resource stack amount
- special event count

Current runtime rebirth flow already applies realm, survived rounds, and rare resource stack settlement. Special event count is wired as a supported dimension in the service API and remains ready for fuller runtime sourcing in later iterations.

## Deferred Items

- No production/consumption loop has been added yet for herbs, ores, breakthrough materials, or rare materials.
- Event option requirements still read legacy resource fields first and do not yet consume unified stack resources as generic costs.
- Breakthrough does not yet consume `required_materials`; the field is present only to stabilize the config shape.
- Rebirth settlement does not yet derive special event count from a dedicated runtime tracker.
- Economy config is still file-backed JSON and not exposed through a dedicated admin workflow.

## MySQL Migration Boundary

- `EconomyConfigRepository` remains the only reader/writer for economy config files.
- `load_resource_definitions`, `RunResourceService`, and `RebirthPointService` consume repository output instead of reading JSON directly in core loop code.
- Core loop services only depend on economy domain helpers and runtime state models, which keeps the future migration path to MySQL at the repository boundary.

## Verification

- `python -m pytest tests/backend/test_economy_config_repository.py -q`
- `python -m pytest tests/backend/test_resource_catalog.py -q`
- `python -m pytest tests/backend/test_run_economy_state.py -q`
- `python -m pytest tests/backend/test_rebirth_point_service.py -q`
- `python -m pytest tests/backend/test_run_rebirth_economy.py -q`
- `python -m pytest tests/backend/test_event_economy_resources.py -q`
- `python -m pytest tests/backend/test_breakthrough_economy_requirements.py -q`
