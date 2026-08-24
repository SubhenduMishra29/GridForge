# ============================================================

# File: core/application/command_handlers.py

# GridForge V2 — Headless Application Command Handlers

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 headless Application command handlers.

Handlers are the translation boundary between immutable
Application commands and Application services.

## Execution boundary

```
CommandManager
      |
      v
Command Handler
      |
      v
ModelService
      |
      v
Core Network / Core Model
```

Handlers may:

```
* validate command payload structure;
* resolve stable endpoint identifiers;
* call Application services;
* register inverse Network operations with Transaction.
```

Handlers must NOT:

```
* mutate Core directly;
* construct Application services repeatedly;
* commit transactions;
* rollback transactions;
* modify history;
* access Qt;
* access UI;
* access SLD/canvas;
* manipulate graphics objects.
```

## Canonical model commands

```
CREATE_BUS
DELETE_BUS
CREATE_LINE
DELETE_LINE
CREATE_TRANSFORMER
DELETE_TRANSFORMER
```

## Endpoint rule

Line and Transformer commands carry endpoint Bus identifiers.

The handler resolves those identifiers against the canonical
ApplicationContext Network and passes the canonical Bus objects
to ModelService.

The handler does not manipulate physical terminals directly.
"""

from **future** import annotations

from typing import Any

from .command import Command
from .command_manager import CommandManager
from .context import ApplicationContext
from .errors import (
ExecutionError,
ResourceError,
ValidationError,
)
from .results import ApplicationResult
from .transaction import Transaction

from .commands.model_commands import (
CREATE_BUS,
DELETE_BUS,
CREATE_LINE,
DELETE_LINE,
CREATE_TRANSFORMER,
DELETE_TRANSFORMER,
CreateBusCommand,
DeleteBusCommand,
CreateLineCommand,
DeleteLineCommand,
CreateTransformerCommand,
DeleteTransformerCommand,
)

from .services.model_service import ModelService

# ============================================================

# SERVICE RESOLUTION

# ============================================================

def _model_service(
context: ApplicationContext,
) -> ModelService:
"""
Construct the Application model service for this execution.

```
ModelService itself is lightweight and does not own the
Network. The canonical Network remains owned by the
ApplicationContext/Core composition boundary.
"""

if not isinstance(
    context,
    ApplicationContext,
):
    raise TypeError(
        "Handler context must be an ApplicationContext."
    )

try:
    return ModelService(
        context,
    )

except Exception as exc:
    raise ExecutionError(
        code="MODEL_SERVICE_INITIALIZATION_FAILED",
        message=(
            "Failed to initialize the Application "
            "ModelService."
        ),
        cause=exc,
    ) from exc
```

# ============================================================

# PAYLOAD HELPERS

# ============================================================

def _require_string(
payload: Any,
field: str,
) -> str:
"""
Extract a required non-empty string from a command payload.
"""

```
if not isinstance(
    payload,
    dict,
):
    try:
        value = payload[field]
    except Exception as exc:
        raise ValidationError(
            code="INVALID_COMMAND_PAYLOAD",
            message=(
                "Command payload must provide "
                f"'{field}'."
            ),
            details={
                "field": field,
            },
        ) from exc
else:
    value = payload.get(field)

if not isinstance(
    value,
    str,
):
    raise ValidationError(
        code="INVALID_COMMAND_FIELD",
        message=(
            f"Command field '{field}' "
            "must be a string."
        ),
        details={
            "field": field,
        },
    )

value = value.strip()

if not value:
    raise ValidationError(
        code="EMPTY_COMMAND_FIELD",
        message=(
            f"Command field '{field}' "
            "must not be empty."
        ),
        details={
            "field": field,
        },
    )

return value
```

def _optional_string(
payload: Any,
field: str,
default: str = "",
) -> str:
"""
Extract an optional string command field.
"""

```
value = payload.get(
    field,
    default,
)

if value is None:
    return default

if not isinstance(
    value,
    str,
):
    raise ValidationError(
        code="INVALID_COMMAND_FIELD",
        message=(
            f"Command field '{field}' "
            "must be a string."
        ),
        details={
            "field": field,
        },
    )

return value.strip()
```

def _number(
payload: Any,
field: str,
*,
default: float | None = None,
) -> float:
"""
Extract a numeric command field.

```
bool is explicitly rejected because bool is a subclass of int.
"""

if field not in payload:

    if default is not None:
        return default

    raise ValidationError(
        code="MISSING_COMMAND_FIELD",
        message=(
            f"Command field '{field}' "
            "is required."
        ),
        details={
            "field": field,
        },
    )

value = payload[field]

if isinstance(
    value,
    bool,
) or not isinstance(
    value,
    (int, float),
):
    raise ValidationError(
        code="INVALID_COMMAND_FIELD",
        message=(
            f"Command field '{field}' "
            "must be numeric."
        ),
        details={
            "field": field,
        },
    )

return float(value)
```

def _object_from_result(
result: ApplicationResult,
*,
command_type: str,
) -> Any:
"""
Require a canonical Core object in ApplicationResult.value.
"""

```
if not isinstance(
    result,
    ApplicationResult,
):
    raise ExecutionError(
        code="INVALID_SERVICE_RESULT",
        message=(
            f"Service for '{command_type}' "
            "did not return an ApplicationResult."
        ),
        details={
            "command_type": command_type,
        },
    )

if not result.success:
    return None

if result.value is None:
    raise ExecutionError(
        code="MISSING_SERVICE_RESULT_VALUE",
        message=(
            f"Service for '{command_type}' "
            "returned success without a value."
        ),
        details={
            "command_type": command_type,
        },
    )

return result.value
```

# ============================================================

# NETWORK RESOLUTION

# ============================================================

def _find_bus(
context: ApplicationContext,
bus_id: str,
) -> Any:
"""
Resolve a canonical Core Bus by stable identifier.
"""

```
network = context.network

for bus in network.buses:

    if getattr(
        bus,
        "id",
        None,
    ) == bus_id:

        return bus

raise ResourceError(
    code="BUS_NOT_FOUND",
    message=(
        f"Bus '{bus_id}' is not registered "
        "on the Core Network."
    ),
    details={
        "bus_id": bus_id,
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
Handle CreateBusCommand.
"""

```
if not isinstance(
    command,
    CreateBusCommand,
):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "CREATE_BUS handler received an "
            "incompatible command."
        ),
    )

payload = command.payload

bus_id = _require_string(
    payload,
    "bus_id",
)

name = _optional_string(
    payload,
    "name",
)

bus_type = payload.get(
    "bus_type",
)

if bus_type is None:
    from core.model.bus import BusType

    bus_type = BusType.PQ

voltage = _number(
    payload,
    "voltage",
    default=1.0,
)

angle = _number(
    payload,
    "angle",
    default=0.0,
)

p_spec = _number(
    payload,
    "p_spec",
    default=0.0,
)

q_spec = _number(
    payload,
    "q_spec",
    default=0.0,
)

v_setpoint = None

if "v_setpoint" in payload:
    value = payload["v_setpoint"]

    if value is not None:
        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise ValidationError(
                code="INVALID_COMMAND_FIELD",
                message=(
                    "Command field 'v_setpoint' "
                    "must be numeric or None."
                ),
                details={
                    "field": "v_setpoint",
                },
            )

        v_setpoint = float(value)

q_min = _number(
    payload,
    "q_min",
    default=float("-inf"),
)

q_max = _number(
    payload,
    "q_max",
    default=float("inf"),
)

service = _model_service(
    context,
)

result = service.create_bus(
    bus_id=bus_id,
    name=name,
    bus_type=bus_type,
    voltage=voltage,
    angle=angle,
    p_spec=p_spec,
    q_spec=q_spec,
    v_setpoint=v_setpoint,
    q_min=q_min,
    q_max=q_max,
)

bus = _object_from_result(
    result,
    command_type=CREATE_BUS,
)

if bus is not None:
    transaction.record_undo(
        lambda bus=bus: context.network.remove_bus(
            bus
        )
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
Handle DeleteBusCommand.
"""

```
if not isinstance(
    command,
    DeleteBusCommand,
):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "DELETE_BUS handler received an "
            "incompatible command."
        ),
    )

bus_id = _require_string(
    command.payload,
    "bus_id",
)

service = _model_service(
    context,
)

result = service.delete_bus(
    bus_id=bus_id,
)

bus = _object_from_result(
    result,
    command_type=DELETE_BUS,
)

if bus is not None:
    transaction.record_undo(
        lambda bus=bus: context.network.add_bus(
            bus
        )
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
Handle CreateLineCommand.
"""

```
if not isinstance(
    command,
    CreateLineCommand,
):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "CREATE_LINE handler received an "
            "incompatible command."
        ),
    )

payload = command.payload

line_id = _require_string(
    payload,
    "line_id",
)

from_bus_id = _require_string(
    payload,
    "endpoint_from",
)

to_bus_id = _require_string(
    payload,
    "endpoint_to",
)

if from_bus_id == to_bus_id:
    raise ValidationError(
        code="IDENTICAL_LINE_ENDPOINTS",
        message=(
            "Line endpoints must reference "
            "different buses."
        ),
        details={
            "endpoint_from": from_bus_id,
            "endpoint_to": to_bus_id,
        },
    )

endpoint_from = _find_bus(
    context,
    from_bus_id,
)

endpoint_to = _find_bus(
    context,
    to_bus_id,
)

r = _number(
    payload,
    "r",
)

x = _number(
    payload,
    "x",
)

b = _number(
    payload,
    "b",
    default=0.0,
)

name = _optional_string(
    payload,
    "name",
)

rate_mva = _number(
    payload,
    "rate_mva",
    default=100.0,
)

service = _model_service(
    context,
)

result = service.create_line(
    line_id=line_id,
    endpoint_from=endpoint_from,
    endpoint_to=endpoint_to,
    r=r,
    x=x,
    b=b,
    name=name,
    rate_mva=rate_mva,
)

line = _object_from_result(
    result,
    command_type=CREATE_LINE,
)

if line is not None:
    transaction.record_undo(
        lambda line=line: context.network.remove_line(
            line
        )
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
Handle DeleteLineCommand.
"""

```
if not isinstance(
    command,
    DeleteLineCommand,
):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "DELETE_LINE handler received an "
            "incompatible command."
        ),
    )

line_id = _require_string(
    command.payload,
    "line_id",
)

service = _model_service(
    context,
)

result = service.delete_line(
    line_id=line_id,
)

line = _object_from_result(
    result,
    command_type=DELETE_LINE,
)

if line is not None:
    transaction.record_undo(
        lambda line=line: context.network.add_line(
            line
        )
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
Handle CreateTransformerCommand.
"""

```
if not isinstance(
    command,
    CreateTransformerCommand,
):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "CREATE_TRANSFORMER handler received "
            "an incompatible command."
        ),
    )

payload = command.payload

transformer_id = _require_string(
    payload,
    "transformer_id",
)

from_bus_id = _require_string(
    payload,
    "endpoint_from",
)

to_bus_id = _require_string(
    payload,
    "endpoint_to",
)

if from_bus_id == to_bus_id:
    raise ValidationError(
        code="IDENTICAL_TRANSFORMER_ENDPOINTS",
        message=(
            "Transformer endpoints must reference "
            "different buses."
        ),
        details={
            "endpoint_from": from_bus_id,
            "endpoint_to": to_bus_id,
        },
    )

endpoint_from = _find_bus(
    context,
    from_bus_id,
)

endpoint_to = _find_bus(
    context,
    to_bus_id,
)

r = _number(
    payload,
    "r",
)

x = _number(
    payload,
    "x",
)

tap = _number(
    payload,
    "tap",
    default=1.0,
)

shift = _number(
    payload,
    "shift",
    default=0.0,
)

name = _optional_string(
    payload,
    "name",
)

rate_mva = _number(
    payload,
    "rate_mva",
    default=100.0,
)

service = _model_service(
    context,
)

result = service.create_transformer(
    transformer_id=transformer_id,
    endpoint_from=endpoint_from,
    endpoint_to=endpoint_to,
    r=r,
    x=x,
    tap=tap,
    shift=shift,
    name=name,
    rate_mva=rate_mva,
)

transformer = _object_from_result(
    result,
    command_type=CREATE_TRANSFORMER,
)

if transformer is not None:
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
Handle DeleteTransformerCommand.
"""

```
if not isinstance(
    command,
    DeleteTransformerCommand,
):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "DELETE_TRANSFORMER handler received "
            "an incompatible command."
        ),
    )

transformer_id = _require_string(
    command.payload,
    "transformer_id",
)

service = _model_service(
    context,
)

result = service.delete_transformer(
    transformer_id=transformer_id,
)

transformer = _object_from_result(
    result,
    command_type=DELETE_TRANSFORMER,
)

if transformer is not None:
    transaction.record_undo(
        lambda transformer=transformer:
        context.network.add_transformer(
            transformer
        )
    )

return result
```

# ============================================================

# REGISTRATION

# ============================================================

def register_model_handlers(
command_manager: CommandManager,
) -> None:
"""
Register the six canonical model command handlers.

```
Registration is deterministic and idempotence is deliberately
NOT provided by this function. Duplicate registration is a
configuration error and is surfaced by CommandManager.
"""

if not isinstance(
    command_manager,
    CommandManager,
):
    raise TypeError(
        "register_model_handlers requires "
        "a CommandManager."
    )

registrations = (
    (
        CREATE_BUS,
        handle_create_bus,
    ),
    (
        DELETE_BUS,
        handle_delete_bus,
    ),
    (
        CREATE_LINE,
        handle_create_line,
    ),
    (
        DELETE_LINE,
        handle_delete_line,
    ),
    (
        CREATE_TRANSFORMER,
        handle_create_transformer,
    ),
    (
        DELETE_TRANSFORMER,
        handle_delete_transformer,
    ),
)

for command_type, handler in registrations:

    command_manager.register(
        command_type,
        handler,
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
