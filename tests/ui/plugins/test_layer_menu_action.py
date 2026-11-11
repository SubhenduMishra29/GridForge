from ui.plugins.menu_plugin import MenuSubmenuSpec, default_menus


def test_sld_layers_is_exposed_in_view_panels_menu():
    view_menu = next(menu for menu in default_menus() if menu.menu_id == "view")
    panels_menu = next(
        item for item in view_menu.actions
        if isinstance(item, MenuSubmenuSpec) and item.menu_id == "view.panels"
    )

    assert any(
        getattr(item, "action_id", None) == "view.layers"
        and item.text == "SLD Layers"
        for item in panels_menu.items
    )
