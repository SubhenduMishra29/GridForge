# -------- TOOL --------
set_tool(name: str)

# -------- CREATION --------
create_bus(x: float, y: float)
create_line(bus_a, bus_b)

# -------- SELECTION --------
set_selection(objects: list)
toggle_selection(obj)
clear_selection()

# -------- DELETE --------
delete_selected()

# -------- FILE --------
save(path)
load(path)
