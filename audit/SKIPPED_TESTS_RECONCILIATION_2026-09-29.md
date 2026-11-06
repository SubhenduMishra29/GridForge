# GridForge V2 — 32 Skipped Tests Reconciliation

Date: 2026-09-29  
Implementation evidence baseline: `c4bb4cdd28b73aa9c7b811588ebad9a083cdc295`  
Current implementation branch after documentation-only authority correction: `282ad5fc53e20bbfc264171df28fbe1a90d21226`

## Evidence

A temporary collection-only diagnostic workflow was used on a disposable verification branch to enumerate the exact skipped tests without launching the GUI. The diagnostic reported **SKIP_COUNT 32**. The normal current-HEAD CI run remains authoritative for execution: **1081 passed / 32 skipped / 0 failed / 0 errors**.

No skipped test was removed merely to increase the pass count.

## Disposition rules

- **STALE_CONTRACT** — historical API/architecture contract retired by V2; replacement current coverage exists.
- **HISTORICAL_TEST** — RED-phase/historical requirement retained only for provenance; current architecture coverage supersedes it.
- **TEST_FIXTURE_DEFECT** — underlying behavior remains active, but the old fixture cannot represent the current authoritative composition/fixture contract. Current integration coverage is used where identified.
- **REQUIRED_BEHAVIOR_WITH_MISSING_COVERAGE** — not accepted silently; none of the 32 skips is classified this way from the evidence reviewed here.
- **VALID_CURRENT_SKIP** — genuinely optional/non-applicable; none identified in this inventory.

No Master ID is assigned where the test itself does not contain an explicit register identifier; this avoids inventing historical linkage.

| # | Test | Reason | Classification | Requirement active? | Replacement/current coverage | Master ID |
|---:|---|---|---|---|---|---|
| 1 | `tests/core/analysis/test_contingency_bus_outage_isolation.py::test_bus_outage_uses_isolated_network_and_leaves_base_unchanged` | Legacy `resolve_terminal_bus` contract retired; current contingency resolves through Network identity/isolated topology. | STALE_CONTRACT | Yes | Current contingency/network preparation and topology tests use the authoritative Network boundary. | Not explicit |
| 2 | `tests/core/analysis/test_contingency_bus_outage_isolation.py::test_bus_outage_semantics_are_distinct_from_element_outage` | Same retired contingency helper/contract. | STALE_CONTRACT | Yes | Current contingency coverage exercises the current outage/topology boundary. | Not explicit |
| 3 | `tests/core/analysis/test_power_flow_gf_aud_207_208.py::test_study_configuration_requires_positive_finite_base_mva` | Historical RED-phase GF-AUD-207/208 fixture. | HISTORICAL_TEST | No as a historical fixture | Current Power Flow configuration/preparation boundary tests. | GF-AUD-207/208 historical |
| 4 | `tests/core/analysis/test_power_flow_gf_aud_207_208.py::test_study_configuration_exposes_immutable_base_mva` | Historical RED-phase fixture. | HISTORICAL_TEST | No as a historical fixture | Current Power Flow configuration/preparation tests. | GF-AUD-207/208 historical |
| 5 | `tests/core/analysis/test_power_flow_gf_aud_207_208.py::test_preparation_normalizes_engineering_power_using_study_base_mva` | Historical RED-phase fixture. | HISTORICAL_TEST | No as a historical fixture | Current Power Flow preparation tests. | GF-AUD-207/208 historical |
| 6 | `tests/core/analysis/test_power_flow_gf_aud_207_208.py::test_preparation_normalizes_generator_q_limits_using_study_base_mva` | Historical RED-phase fixture. | HISTORICAL_TEST | No as a historical fixture | Current Power Flow preparation tests. | GF-AUD-207/208 historical |
| 7 | `tests/core/analysis/test_power_flow_gf_aud_207_208.py::test_preparation_does_not_use_hard_coded_100_mva_base` | Historical RED-phase fixture. | HISTORICAL_TEST | No as a historical fixture | Current Power Flow preparation tests. | GF-AUD-207/208 historical |
| 8 | `tests/core/analysis/test_power_flow_gf_aud_207_208.py::test_voltage_normalization_uses_each_bus_nominal_voltage` | Historical RED-phase fixture. | HISTORICAL_TEST | No as a historical fixture | Current Power Flow preparation/result conversion tests. | GF-AUD-207/208 historical |
| 9 | `tests/core/analysis/test_power_flow_gf_aud_207_208.py::test_prepared_power_flow_remains_immutable` | Historical RED-phase fixture. | HISTORICAL_TEST | No as a historical fixture | Current PreparedPowerFlow boundary tests. | GF-AUD-207/208 historical |
| 10 | `tests/core/analysis/test_power_flow_gf_aud_207_208.py::test_preparation_preserves_canonical_bus_order_for_input_and_ybus` | Historical RED-phase fixture. | HISTORICAL_TEST | No as a historical fixture | Current preparation/YBus boundary tests. | GF-AUD-207/208 historical |
| 11 | `tests/core/analysis/test_power_flow_gf_aud_207_208.py::test_result_conversion_uses_bus_specific_nominal_voltage_not_global_base` | Historical RED-phase fixture. | HISTORICAL_TEST | No as a historical fixture | Current result conversion tests. | GF-AUD-207/208 historical |
| 12 | `tests/core/analysis/test_power_flow_gf_aud_207_208.py::test_boundary_result_is_structured_engineering_data_not_display_text` | Historical RED-phase fixture. | HISTORICAL_TEST | No as a historical fixture | Current Power Flow result contract tests. | GF-AUD-207/208 historical |
| 13 | `tests/core/analysis/test_short_circuit_preparation_boundary.py::test_fault_bus_resolution_is_local_and_does_not_require_network_indexing` | Old constructor/sequence-preparation boundary. | STALE_CONTRACT | Yes | Current short-circuit sequence/preparation boundary tests. | Not explicit |
| 14 | `tests/core/analysis/test_short_circuit_preparation_boundary.py::test_three_phase_preparation_requires_declared_positive_sequence_matrix` | Old constructor/sequence-preparation boundary. | STALE_CONTRACT | Yes | Current short-circuit sequence/preparation boundary tests. | Not explicit |
| 15 | `tests/core/application/test_control_cycle.py::test_application_facade_owns_control_cycle_orchestration` | Legacy engine-injection fixture; current execution requires active project + committed ControlConfiguration. | STALE_CONTRACT | Yes | Current Application control-cycle execution/diagnostic tests. | Not explicit |
| 16 | `tests/core/application/test_control_cycle.py::test_application_control_cycle_uses_application_event_publication_path` | Retired ElementUpdated/NetworkChanged event expectation. | STALE_CONTRACT | Yes | Current ControlExecutionStarted/Completed event contract tests. | Not explicit |
| 17 | `tests/core/application/test_current_head_protection_closure.py::test_protection_configuration_requires_existing_relay_and_blocks_relay_delete` | Legacy fixture lacks authoritative MeasurementChannel provisioning. | TEST_FIXTURE_DEFECT | Yes | Current protection lifecycle/execution tests use the provisioned measurement boundary. | Not explicit |
| 18 | `tests/core/application/test_current_head_protection_closure.py::test_project_a_protection_state_does_not_leak_into_project_b_and_reopens` | Legacy fixture lacks authoritative MeasurementChannel provisioning. | TEST_FIXTURE_DEFECT | Yes | Current project protection lifecycle coverage exists; old fixture requires migration if this exact isolation assertion is still required. | Not explicit |
| 19 | `tests/ui/events/test_application_event_projection_path.py::test_application_event_reaches_sld_projection_without_core_callback` | Direct UIUpdateBoundary→SLDUpdateCoordinator fixture retired in favor of UIProjectionCoordinator. | HISTORICAL_TEST | No as historical fixture | Current coordinator integration coverage. | Not explicit |
| 20 | `tests/ui/test_bus_creation_command_contract.py::test_bus_tool_submits_authoritative_create_bus_command_through_application` | Pre-CreationContext BusTool fixture. | STALE_CONTRACT | Yes | CreationContext-aware placement tests and 17-test SLD regression gate. | Not explicit |
| 21 | `tests/ui/test_composition_root_contract.py::test_real_properties_panel_is_injected_before_selection_projection_is_used` | Legacy composition fixture lacks mandatory SLD projection/render services. | TEST_FIXTURE_DEFECT | Yes | Current full CanvasComposer composition test. | Not explicit |
| 22 | `tests/ui/test_lifecycle_failure_isolation.py::test_open_without_saved_presentation_creates_canonical_sld_document` | Legacy StubApplication lacks current project-lifecycle presentation transaction interface. | TEST_FIXTURE_DEFECT | Yes | Current project/workspace lifecycle integration coverage; exact legacy assertion should be migrated if retained as a distinct requirement. | Not explicit |
| 23 | `tests/ui/test_lifecycle_failure_isolation.py::test_ui_activation_failure_closes_new_application_project` | Legacy StubApplication lacks current project-lifecycle presentation transaction interface. | TEST_FIXTURE_DEFECT | Yes | Current project/workspace lifecycle integration coverage. | Not explicit |
| 24 | `tests/ui/test_transformer_tool.py::test_transformer_tool_metadata_and_lifecycle` | Pre-CreationContext immutable draft-placement fixture. | STALE_CONTRACT | Yes | CreationContext-aware tool tests and targeted SLD regression gate. | Not explicit |
| 25 | `tests/ui/test_transformer_tool.py::test_mouse_press_captures_snapped_transformer_position` | Pre-CreationContext fixture. | STALE_CONTRACT | Yes | Current CreationContext/snap placement coverage. | Not explicit |
| 26 | `tests/ui/test_transformer_tool.py::test_mouse_release_refuses_unconfirmed_core_mutation` | Pre-CreationContext fixture. | STALE_CONTRACT | Yes | Current immutable draft/Application commit boundary tests. | Not explicit |
| 27 | `tests/ui/test_transformer_tool.py::test_escape_cancels_transient_transformer_placement` | Pre-CreationContext fixture. | STALE_CONTRACT | Yes | Current CreationContext-aware placement tests. | Not explicit |
| 28 | `tests/ui/tools/test_equipment_tool_command_paths.py::test_cable_tool_executes_create_cable_command_through_application` | Legacy tool fixture predates CreationContext immutable draft workflow. | STALE_CONTRACT | Yes | Current CreationContext-aware tool/command tests and targeted SLD regression gate. | Not explicit |
| 29 | `tests/ui/tools/test_equipment_tool_command_paths.py::test_transformer_tool_executes_create_transformer_command_through_application` | Legacy tool fixture predates CreationContext immutable draft workflow. | STALE_CONTRACT | Yes | Current CreationContext-aware tool/command tests and targeted SLD regression gate. | Not explicit |
| 30 | `tests/ui/tools/test_line_tool_engineering_configuration.py::test_line_tool_uses_ui_entered_parameters_in_canonical_command` | Legacy tool fixture predates CreationContext immutable draft workflow. | STALE_CONTRACT | Yes | Current CreationContext-aware line/tool workflow coverage. | Not explicit |
| 31 | `tests/ui/tools/test_line_tool_engineering_configuration.py::test_line_tool_rejects_missing_engineering_parameters` | Legacy tool fixture predates CreationContext immutable draft workflow. | STALE_CONTRACT | Yes | Current CreationContext-aware line/tool workflow coverage. | Not explicit |
| 32 | `tests/ui/tools/test_line_tool_engineering_configuration.py::test_line_tool_does_not_read_engineering_parameters_from_controller` | Legacy tool fixture predates CreationContext immutable draft workflow. | STALE_CONTRACT | Yes | Current CreationContext-aware line/tool workflow coverage. | Not explicit |

## Closure decision on skips

The 32 skips are **justified classifications**, not an assertion that every skipped historical assertion has been reimplemented one-for-one. Two fixture-defect groups (#18, #22–23) retain active requirements that should remain represented by current integration coverage; the current suite contains replacement lifecycle coverage, but those exact old fixture assertions were not silently treated as runtime-proven GUI behavior.

No skip is classified VALID_CURRENT_SKIP. No skip is classified REQUIRED_BEHAVIOR_WITH_MISSING_COVERAGE based on the current evidence review, with the fixture-defect cases explicitly called out above for continued coverage attention.

The skipped population therefore does not constitute a hidden functional-failure bucket in the current green CI run, but GUI/runtime acceptance remains separately pending.
