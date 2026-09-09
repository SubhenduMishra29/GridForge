from core.errors import (
    CoreError,
    InfrastructureError,
    InvalidCallerContractError,
    InvalidDomainStateError,
    InvalidStructuralRelationshipError,
)


def test_core_error_categories_share_one_domain_root() -> None:
    categories = (
        InvalidCallerContractError,
        InvalidDomainStateError,
        InvalidStructuralRelationshipError,
        InfrastructureError,
    )

    assert all(issubclass(error_type, CoreError) for error_type in categories)


def test_core_error_categories_are_distinct() -> None:
    categories = {
        InvalidCallerContractError,
        InvalidDomainStateError,
        InvalidStructuralRelationshipError,
        InfrastructureError,
    }

    assert len(categories) == 4
