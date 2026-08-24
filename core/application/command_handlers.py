# ============================================================

# File: core/application/command_handlers.py

# GridForge V2 — Headless Application Command Handlers

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2
============

Module:
core.application.command_handlers

## Purpose

Connect immutable Application Commands to Application Services.

## Frozen execution contract

```
CommandManager
      |
      v
handler(command, context, transaction)
      |
      v
  ModelService
      |
      v
     Core
```

Handlers perform Application-level orchestration only.

They do NOT:

```
* mutate Core directly;
* manipulate Network collections directly;
* manipulate topology;
* build Y-bus;
* invalidate derived state manually;
* access Qt;
* create graphics objects;
* render SLD objects;
* commit transactions;
* rollback transactions;
* manipulate command history.
```

## Transaction responsibility

Handlers register inverse operations through:

```
transaction.record_undo(...)
```

CommandManager owns:

```
* transaction creation;
* commit;
* rollback;
* history recording.
```

## Endpoint resolution

The current Terminal model does not expose a stable independent
Terminal ID.

Therefore:

```
endpoint_from_id
endpoint_to_id
```

are resolved against canonical Network Bus IDs.

The handler passes the canonical Bus objects to ModelService.

This rule is intentionally conservative and remains frozen until
a stable Terminal identity contract is introduced.
"""

from **future** import annotations

from typing import Any

from core.model import Bus

from .command import Command
from .commands.model_commands import (
CREATE_BUS,
DELETE_BUS,
CREATE_LINE,
DELETE_LINE,
CREATE_TRANSFORMER,
DELETE_TRANSFORMER,
)
from .context import ApplicationContext
from .errors import ExecutionError, ResourceError
from .results import ApplicationResult
from .services.model_service import ModelService
from .transaction import Transaction

# ============================================================

# INTERNAL SERVICE FACTORY

# ============================================================

def _service(
context: ApplicationContext,
) -> ModelService:
"""
Construct the Application ModelService.

```
ModelService remains stateless with respect to the canonical
Network and receives the Application context explicitly.
"""

if not isinstance(
    context,
    ApplicationContext,
):
    raise TypeError(
        "Command handler requires an ApplicationContext."
    )

return ModelService(context)
```

# ============================================================

# PAYLOAD ACCESS

# ============================================================

def _payload_value(
command: Command,
key: str,
) -> Any:
"""
Read a required command payload value.
"""

```
try:
    return command.payload[key]

except KeyError as exc:

    raise ExecutionError(
        code="COMMAND_PAYLOAD_FIELD_MISSING",
        message=(
            f"Command '{command.command_type}' is missing "
            f"required payload field '{key}'."
        ),
        details={
            "command_type": command.command_type,
            "command_id": str(
                command.command_id
            ),
            "field": key,
        },
        cause=exc,
    ) from exc
```

# ============================================================

# COMMAND TYPE VALIDATION

# ============================================================

def _require_command_type(
command: Command,
expected: str,
) -> None:
"""
Ensure a handler receives its registered command type.
"""

```
if command.command_type != expected:

    raise ExecutionError(
        code="COMMAND_TYPE_MISMATCH",
        message=(
            f"Handler expected command type '{expected}' "
            f"but received '{command.command_type}'."
        ),
        details={
            "expected": expected,
            "received": command.command_type,
            "command_id": str(
                command.command_id
            ),
        },
    )
```

# ============================================================

# BUS RESOLUTION

# ============================================================

def _find_bus(
context: ApplicationContext,
bus_id: str,
) -> Bus:
"""
Resolve a canonical Bus by Network identifier.

```
Lookup only.

This function never mutates Network.
"""

if not isinstance(
    bus_id,
    str,
) or not bus_id.strip():

    raise ExecutionError(
        code="INVALID_ENDPOINT_ID",
        message=(
            "Endpoint identifier must be "
            "a non-empty string."
        ),
        details={
            "endpoint_id": bus_id,
        },
    )

normalized_id = bus_id.strip()

for bus in context.network.buses:

    if getattr(
        bus,
        "id",
        None,
    ) == normalized_id:

        return bus

raise ResourceError(
    code="LINE_ENDPOINT_BUS_NOT_FOUND",
    message=(
        f"Endpoint Bus '{normalized_id}' "
        "is not registered on the Core Network."
    ),
    details={
        "bus_id": normalized_id,
    },
)
```

# ============================================================

# CREATE BUS

# ============================================================

def handle_create_bus(
command: Command,
context: ApplicationContext,
transaction: Transaction,
) -> ApplicationResult:
"""
Execute CreateBusCommand.

```
ModelService performs the actual Core mutation.

The newly created Bus is registered for inverse removal.
"""

_require_command_type(
    command,
    CREATE_BUS,
)

service = _service(context)

result = service.create_bus(
    bus_id=_payload_value(
        command,
        "bus_id",
    ),
    name=_payload_value(
        command,
        "name",
    ),
    bus_type=_payload_value(
        command,
        "bus_type",
    ),
    voltage=_payload_value(
        command,
        "voltage",
    ),
    angle=_payload_value(
        command,
        "angle",
    ),
    p_spec=_payload_value(
        command,
        "p_spec",
    ),
    q_spec=_payload_value(
        command,
        "q_spec",
    ),
    v_setpoint=_payload_value(
        command,
        "v_setpoint",
    ),
    q_min=_payload_value(
        command,
        "q_min",
    ),
    q_max=_payload_value(
        command,
        "q_max",
    ),
)

bus = result.value

transaction.record_undo(
    lambda bus=bus:
        context.network.remove_bus(bus)
)

return result
```

# ============================================================

# DELETE BUS

# ============================================================

def handle_delete_bus(
command: Command,
context: ApplicationContext,
transaction: Transaction,
) -> ApplicationResult:
"""
Execute DeleteBusCommand.

```
The removed canonical Bus is registered for inverse
restoration.

Network.add_bus() owns restoration of Network membership.
"""

_require_command_type(
    command,
    DELETE_BUS,
)

service = _service(context)

result = service.delete_bus(
    bus_id=_payload_value(
        command,
        "bus_id",
    ),
)

bus = result.value

transaction.record_undo(
    lambda bus=bus:
        context.network.add_bus(bus)
)

return result
```

# ============================================================

# CREATE LINE

# ============================================================

def handle_create_line(
command: Command,
context: ApplicationContext,
transaction: Transaction,
) -> ApplicationResult:
"""
Execute CreateLineCommand.

```
endpoint_from_id and endpoint_to_id are resolved as canonical
Network Bus IDs.

ModelService owns Line construction and Network mutation.
"""

_require_command_type(
    command,
    CREATE_LINE,
)

endpoint_from = _find_bus(
    context,
    _payload_value(
        command,
        "endpoint_from_id",
    ),
)

endpoint_to = _find_bus(
    context,
    _payload_value(
        command,
        "endpoint_to_id",
    ),
)

service = _service(context)

result = service.create_line(
    line_id=_payload_value(
        command,
        "line_id",
    ),
    endpoint_from=endpoint_from,
    endpoint_to=endpoint_to,
    r=_payload_value(
        command,
        "r",
    ),
    x=_payload_value(
        command,
        "x",
    ),
    b=_payload_value(
        command,
        "b",
    ),
    name=_payload_value(
        command,
        "name",
    ),
    rate_mva=_payload_value(
        command,
        "rate_mva",
    ),
)

line = result.value

transaction.record_undo(
    lambda line=line:
        context.network.remove_line(line)
)

return result
```

# ============================================================

# DELETE LINE

# ============================================================

def handle_delete_line(
command: Command,
context: ApplicationContext,
transaction: Transaction,
) -> ApplicationResult:
"""
Execute DeleteLineCommand.

```
The exact canonical Line object returned by the service is
registered for inverse restoration.

Terminal manipulation is intentionally absent here.
Network owns membership and topology consequences.
"""

_require_command_type(
    command,
    DELETE_LINE,
)

service = _service(context)

result = service.delete_line(
    line_id=_payload_value(
        command,
        "line_id",
    ),
)

line = result.value

transaction.record_undo(
    lambda line=line:
        context.network.add_line(line)
)

return result
```

# ============================================================

# CREATE TRANSFORMER

# ============================================================

def handle_create_transformer(
command: Command,
context: ApplicationContext,
transaction: Transaction,
) -> ApplicationResult:
"""
Execute CreateTransformerCommand.

```
Endpoint identifiers are resolved as canonical Network Bus IDs.

ModelService owns Transformer construction and Network
membership.
"""

_require_command_type(
    command,
    CREATE_TRANSFORMER,
)

endpoint_from = _find_bus(
    context,
    _payload_value(
        command,
        "endpoint_from_id",
    ),
)

endpoint_to = _find_bus(
    context,
    _payload_value(
        command,
        "endpoint_to_id",
    ),
)

service = _service(context)

result = service.create_transformer(
    transformer_id=_payload_value(
        command,
        "transformer_id",
    ),
    endpoint_from=endpoint_from,
    endpoint_to=endpoint_to,
    r=_payload_value(
        command,
        "r",
    ),
    x=_payload_value(
        command,
        "x",
    ),
    tap=_payload_value(
        command,
        "tap",
    ),
    shift=_payload_value(
        command,
        "shift",
    ),
    name=_payload_value(
        command,
        "name",
    ),
    rate_mva=_payload_value(
        command,
        "rate_mva",
    ),
)

transformer = result.value

transaction.record_undo(
    lambda transformer=transformer:
        context.network.remove_transformer(
            transformer
        )
)

return result
```

# ============================================================

# DELETE TRANSFORMER

# ============================================================

def handle_delete_transformer(
command: Command,
context: ApplicationContext,
transaction: Transaction,
) -> ApplicationResult:
"""
Execute DeleteTransformerCommand.

```
The exact canonical Transformer object returned by the
service is registered for inverse restoration.
"""

_require_command_type(
    command,
    DELETE_TRANSFORMER,
)

service = _service(context)

result = service.delete_transformer(
    transformer_id=_payload_value(
        command,
        "transformer_id",
    ),
)

transformer = result.value

transaction.record_undo(
    lambda transformer=transformer:
        context.network.add_transformer(
            transformer
        )
)

return result
```

# ============================================================

# MODEL HANDLER REGISTRATION

# ============================================================

def register_model_handlers(
command_manager,
) -> None:
"""
Register all six canonical model commands.

```
Registration is composition only.

No command is executed here.
"""

if command_manager is None:
    raise ValueError(
        "command_manager must not be None."
    )

command_manager.register(
    CREATE_BUS,
    handle_create_bus,
)

command_manager.register(
    DELETE_BUS,
    handle_delete_bus,
)

command_manager.register(
    CREATE_LINE,
    handle_create_line,
)

command_manager.register(
    DELETE_LINE,
    handle_delete_line,
)

command_manager.register(
    CREATE_TRANSFORMER,
    handle_create_transformer,
)

command_manager.register(
    DELETE_TRANSFORMER,
    handle_delete_transformer,
)
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"handle_create_bus",
"handle_delete_bus",
"handle_create_line",
"handle_delete_line",
"handle_create_transformer",
"handle_delete_transformer",
"register_model_handlers",
]
