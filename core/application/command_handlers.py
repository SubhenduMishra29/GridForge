# ============================================================

# File: core/application/command_handlers.py

# GridForge V2 — Headless Application Command Handlers

# Author: Subhendu Mishra

# ============================================================

"""
Command handlers form the translation boundary between immutable
Application commands and Application Services.

Handlers:

```
* validate command payloads;
* resolve canonical Core endpoints;
* invoke Application Services;
* register inverse operations with Transaction.
```

Handlers do not:

```
* commit or rollback transactions;
* modify CommandHistory;
* mutate Core implementation details directly;
* access UI, Qt, SLD, canvas, or renderers.
```

"""

from **future** import annotations

from collections.abc import Mapping
from typing import Any

from .command import Command
from .context import ApplicationContext
from .errors import ExecutionError, ResourceError, ValidationError
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
"""Resolve the Application ModelService."""

```
if not isinstance(context, ApplicationContext):
    raise TypeError(
        "Handler context must be an ApplicationContext."
    )

try:
    return ModelService(context)
except Exception as exc:
    raise ExecutionError(
        code="MODEL_SERVICE_INITIALIZATION_FAILED",
        message="Failed to initialize the Application ModelService.",
        cause=exc,
    ) from exc
```

# ============================================================

# PAYLOAD VALIDATION

# ============================================================

def _payload_mapping(
command: Command,
) -> Mapping[str, Any]:
"""Return a validated command payload mapping."""

```
payload = command.payload

if not isinstance(payload, Mapping):
    raise ValidationError(
        code="INVALID_COMMAND_PAYLOAD",
        message="Command payload must be a mapping.",
        details={
            "command_type": command.command_type,
        },
    )

return payload
```

def _require_string(
payload: Mapping[str, Any],
field: str,
) -> str:
"""Return a required non-empty string field."""

```
if field not in payload:
    raise ValidationError(
        code="MISSING_COMMAND_FIELD",
        message=f"Command field '{field}' is required.",
        details={"field": field},
    )

value = payload[field]

if not isinstance(value, str):
    raise ValidationError(
        code="INVALID_COMMAND_FIELD",
        message=f"Command field '{field}' must be a string.",
        details={
            "field": field,
            "actual_type": type(value).__name__,
        },
    )

value = value.strip()

if not value:
    raise ValidationError(
        code="EMPTY_COMMAND_FIELD",
        message=f"Command field '{field}' must not be empty.",
        details={"field": field},
    )

return value
```

def _optional_string(
payload: Mapping[str, Any],
field: str,
default: str = "",
) -> str:
"""Return an optional string field."""

```
if field not in payload or payload[field] is None:
    return default

value = payload[field]

if not isinstance(value, str):
    raise ValidationError(
        code="INVALID_COMMAND_FIELD",
        message=f"Command field '{field}' must be a string.",
        details={
            "field": field,
            "actual_type": type(value).__name__,
        },
    )

return value.strip()
```

def _number(
payload: Mapping[str, Any],
field: str,
*,
default: float | None = None,
) -> float:
"""Return a numeric field as float."""

```
if field not in payload:
    if default is not None:
        return float(default)

    raise ValidationError(
        code="MISSING_COMMAND_FIELD",
        message=f"Command field '{field}' is required.",
        details={"field": field},
    )

value = payload[field]

if isinstance(value, bool) or not isinstance(
    value,
    (int, float),
):
    raise ValidationError(
        code="INVALID_COMMAND_FIELD",
        message=f"Command field '{field}' must be numeric.",
        details={
            "field": field,
            "actual_type": type(value).__name__,
        },
    )

return float(value)
```

def _optional_number(
payload: Mapping[str, Any],
field: str,
) -> float | None:
"""Return an optional numeric field."""

```
if field not in payload or payload[field] is None:
    return None

value = payload[field]

if isinstance(value, bool) or not isinstance(
    value,
    (int, float),
):
    raise ValidationError(
        code="INVALID_COMMAND_FIELD",
        message=(
            f"Command field '{field}' must be numeric "
            "or None."
        ),
        details={"field": field},
    )

return float(value)
```

def _service_result(
result: ApplicationResult[Any],
*,
command_type: str,
) -> ApplicationResult[Any]:
"""Validate an Application Service result."""

```
if not isinstance(result, ApplicationResult):
    raise ExecutionError(
        code="INVALID_SERVICE_RESULT",
        message=(
            f"Service for '{command_type}' did not return "
            "an ApplicationResult."
        ),
        details={
            "command_type": command_type,
            "result_type": type(result).__name__,
        },
    )

if not result.is_success:
    raise ExecutionError(
        code="UNSUCCESSFUL_SERVICE_RESULT",
        message=(
            f"Service for '{command_type}' returned "
            "an unsuccessful result."
        ),
        details={
            "command_type": command_type,
        },
    )

return result
```

def _result_value(
result: ApplicationResult[Any],
*,
command_type: str,
) -> Any:
"""Require a canonical object in a successful result."""

```
result = _service_result(
    result,
    command_type=command_type,
)

if result.value is None:
    raise ExecutionError(
        code="MISSING_SERVICE_RESULT_VALUE",
        message=(
            f"Service for '{command_type}' returned "
            "no value."
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
"""Resolve a canonical Bus from the Application Network."""

```
network = context.network

buses = getattr(network, "buses", None)

if buses is None:
    raise ExecutionError(
        code="NETWORK_BUS_COLLECTION_UNAVAILABLE",
        message="Core Network does not expose its bus collection.",
    )

for bus in buses:
    if getattr(bus, "id", None) == bus_id:
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
) -> ApplicationResult[Any]:
"""Handle CREATE_BUS."""

```
if not isinstance(command, CreateBusCommand):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "CREATE_BUS handler received an "
            "incompatible command."
        ),
    )

payload = _payload_mapping(command)

bus_id = _require_string(payload, "bus_id")
name = _optional_string(payload, "name")

bus_type = payload.get("bus_type")

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

v_setpoint = _optional_number(
    payload,
    "v_setpoint",
)

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

service = _model_service(context)

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

bus = _result_value(
    result,
    command_type=CREATE_BUS,
)

transaction.record_undo(
    lambda bus=bus: context.network.remove_bus(bus)
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
) -> ApplicationResult[Any]:
"""Handle DELETE_BUS."""

```
if not isinstance(command, DeleteBusCommand):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "DELETE_BUS handler received an "
            "incompatible command."
        ),
    )

payload = _payload_mapping(command)

bus_id = _require_string(
    payload,
    "bus_id",
)

service = _model_service(context)

result = service.delete_bus(
    bus_id=bus_id,
)

bus = _result_value(
    result,
    command_type=DELETE_BUS,
)

transaction.record_undo(
    lambda bus=bus: context.network.add_bus(bus)
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
) -> ApplicationResult[Any]:
"""Handle CREATE_LINE."""

```
if not isinstance(command, CreateLineCommand):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "CREATE_LINE handler received an "
            "incompatible command."
        ),
    )

payload = _payload_mapping(command)

line_id = _require_string(
    payload,
    "line_id",
)

endpoint_from_id = _require_string(
    payload,
    "endpoint_from",
)

endpoint_to_id = _require_string(
    payload,
    "endpoint_to",
)

if endpoint_from_id == endpoint_to_id:
    raise ValidationError(
        code="IDENTICAL_LINE_ENDPOINTS",
        message=(
            "Line endpoints must reference "
            "different buses."
        ),
        details={
            "endpoint_from": endpoint_from_id,
            "endpoint_to": endpoint_to_id,
        },
    )

endpoint_from = _find_bus(
    context,
    endpoint_from_id,
)

endpoint_to = _find_bus(
    context,
    endpoint_to_id,
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

service = _model_service(context)

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

line = _result_value(
    result,
    command_type=CREATE_LINE,
)

transaction.record_undo(
    lambda line=line: context.network.remove_line(line)
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
) -> ApplicationResult[Any]:
"""Handle DELETE_LINE."""

```
if not isinstance(command, DeleteLineCommand):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "DELETE_LINE handler received an "
            "incompatible command."
        ),
    )

payload = _payload_mapping(command)

line_id = _require_string(
    payload,
    "line_id",
)

service = _model_service(context)

result = service.delete_line(
    line_id=line_id,
)

line = _result_value(
    result,
    command_type=DELETE_LINE,
)

transaction.record_undo(
    lambda line=line: context.network.add_line(line)
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
) -> ApplicationResult[Any]:
"""Handle CREATE_TRANSFORMER."""

```
if not isinstance(command, CreateTransformerCommand):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "CREATE_TRANSFORMER handler received an "
            "incompatible command."
        ),
    )

payload = _payload_mapping(command)

transformer_id = _require_string(
    payload,
    "transformer_id",
)

endpoint_from_id = _require_string(
    payload,
    "endpoint_from",
)

endpoint_to_id = _require_string(
    payload,
    "endpoint_to",
)

if endpoint_from_id == endpoint_to_id:
    raise ValidationError(
        code="IDENTICAL_TRANSFORMER_ENDPOINTS",
        message=(
            "Transformer endpoints must reference "
            "different buses."
        ),
        details={
            "endpoint_from": endpoint_from_id,
            "endpoint_to": endpoint_to_id,
        },
    )

endpoint_from = _find_bus(
    context,
    endpoint_from_id,
)

endpoint_to = _find_bus(
    context,
    endpoint_to_id,
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

service = _model_service(context)

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

transformer = _result_value(
    result,
    command_type=CREATE_TRANSFORMER,
)

transaction.record_undo(
    lambda transformer=transformer:
        context.network.remove_transformer(transformer)
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
) -> ApplicationResult[Any]:
"""Handle DELETE_TRANSFORMER."""

```
if not isinstance(command, DeleteTransformerCommand):
    raise ValidationError(
        code="INVALID_COMMAND_TYPE",
        message=(
            "DELETE_TRANSFORMER handler received an "
            "incompatible command."
        ),
    )

payload = _payload_mapping(command)

transformer_id = _require_string(
    payload,
    "transformer_id",
)

service = _model_service(context)

result = service.delete_transformer(
    transformer_id=transformer_id,
)

transformer = _result_value(
    result,
    command_type=DELETE_TRANSFORMER,
)

transaction.record_undo(
    lambda transformer=transformer:
        context.network.add_transformer(transformer)
)

return result
```

# ============================================================

# HANDLER REGISTRY

# ============================================================

COMMAND_HANDLERS: dict[str, Any] = {
CREATE_BUS: handle_create_bus,
DELETE_BUS: handle_delete_bus,
CREATE_LINE: handle_create_line,
DELETE_LINE: handle_delete_line,
CREATE_TRANSFORMER: handle_create_transformer,
DELETE_TRANSFORMER: handle_delete_transformer,
}

def register_model_handlers(
command_manager: Any,
) -> None:
"""Register all model handlers with a CommandManager."""

```
for command_type, handler in COMMAND_HANDLERS.items():
    command_manager.register_handler(
        command_type,
        handler,
    )
```

__all__ = [
"handle_create_bus",
"handle_delete_bus",
"handle_create_line",
"handle_delete_line",
"handle_create_transformer",
"handle_delete_transformer",
"COMMAND_HANDLERS",
"register_model_handlers",
]
