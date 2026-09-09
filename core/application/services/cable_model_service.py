"""Application service boundary for Cable mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.core.model.bus import Bus
from core.core.model.cable import Cable
from core.core.model.terminal import Terminal
from core.core.network.network import Network
