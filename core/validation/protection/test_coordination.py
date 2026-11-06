"""
GridForge Protection Coordination Validation


Validates:

- Primary relay selection
- Backup relay selection
- Coordination margin
- Protection hierarchy


"""



from core.protection.coordination import (

    ProtectionCoordinator

)



from core.protection.relay import Relay





def build_test_relays():


    primary = Relay(

        relay_id="R_PRIMARY",

        pickup_current=1.0

    )


    backup = Relay(

        relay_id="R_BACKUP",

        pickup_current=1.2

    )


    return primary, backup




# =====================================================
# TEST CASES
# =====================================================


def test_primary_backup_assignment():


    primary, backup = build_test_relays()



    coordinator = ProtectionCoordinator()



    coordinator.add_primary(

        primary

    )


    coordinator.add_backup(

        backup

    )



    assert (

        coordinator.primary.id

        ==

        "R_PRIMARY"

    )


    assert (

        coordinator.backup.id

        ==

        "R_BACKUP"

    )




def test_coordination_margin_exists():


    primary, backup = build_test_relays()



    coordinator = ProtectionCoordinator()



    margin = coordinator.calculate_margin(

        primary,

        backup

    )



    assert margin >= 0




def test_primary_trips_before_backup():


    primary, backup = build_test_relays()



    coordinator = ProtectionCoordinator()



    assert coordinator.priority(

        primary,

        backup

    ) == "PRIMARY"
