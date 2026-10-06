    # ToolManager remains the lifecycle authority; Controller only coordinates
    # the explicit cancellation-enabled transition.
    for definition in build_action_definitions(contextual_tool_definitions_all):
        action_id = definition.action_id
        if not action_id.startswith("tool.") or action_router.has(action_id):
            continue
        tool_id = definition.tool_id
        if tool_id is None:
            continue
        if tool_id in tool_manager.get_tool_ids():
            handler = lambda tool_id=tool_id: controller.set_tool(
                tool_id,
                cancel_active_creation=True,
            )
        else:
            editor_types = tuple(definition.metadata.get("editor_types", ()))
            if "control" in editor_types:
                handler = lambda tool_id=tool_id: control_workspace.activate_tool_id(tool_id)
            elif "protection" in editor_types:
                handler = lambda tool_id=tool_id: protection_workspace.activate_tool_id(tool_id)
            elif "study" in editor_types:
                handler = lambda tool_id=tool_id: study_tool_runtime.activate(tool_id)
            else:
                continue
        action_router.register_definition(definition, handler)
