"""
This test tests the happy path for curator permissions
"""
from danswer.db.enums import AccessType
from danswer.db.models import UserRole
from danswer.server.documents.models import DocumentSource
from tests.integration.common_utils.managers.cc_pair import CCPairManager
from tests.integration.common_utils.managers.connector import ConnectorManager
from tests.integration.common_utils.managers.credential import CredentialManager
from tests.integration.common_utils.managers.user import TestUser
from tests.integration.common_utils.managers.user import UserManager
from tests.integration.common_utils.managers.user_group import UserGroupManager


def test_whole_curator_flow(reset: None) -> None:
    # Creating an admin user (first user created is automatically an admin)
    admin_user: TestUser = UserManager.create(name="admin_user")
    assert UserManager.verify_role(admin_user, UserRole.ADMIN)

    # Creating a curator
    curator: TestUser = UserManager.create(name="curator")

    # Creating a user group
    user_group_1 = UserGroupManager.create(
        name="user_group_1",
        user_ids=[curator.id],
        cc_pair_ids=[],
        user_performing_action=admin_user,
    )
    UserGroupManager.wait_for_sync(
        user_groups_to_check=[user_group_1], user_performing_action=admin_user
    )
    # Making curator a curator of user_group_1
    UserGroupManager.set_curator_status(
        test_user_group=user_group_1,
        user_to_set_as_curator=curator,
        user_performing_action=admin_user,
    )
    assert UserManager.verify_role(curator, UserRole.CURATOR)

    # Creating a credential as curator
    test_credential = CredentialManager.create(
        name="curator_test_credential",
        source=DocumentSource.FILE,
        curator_public=False,
        groups=[user_group_1.id],
        user_performing_action=curator,
    )

    # Creating a connector as curator
    test_connector = ConnectorManager.create(
        name="curator_test_connector",
        source=DocumentSource.FILE,
        is_public=False,
        groups=[user_group_1.id],
        user_performing_action=curator,
    )

    # Test editing the connector
    test_connector.name = "updated_test_connector"
    ConnectorManager.edit(connector=test_connector, user_performing_action=curator)

    # Creating a CC pair as curator
    test_cc_pair = CCPairManager.create(
        connector_id=test_connector.id,
        credential_id=test_credential.id,
        name="curator_test_cc_pair",
        access_type=AccessType.PRIVATE,
        groups=[user_group_1.id],
        user_performing_action=curator,
    )

    CCPairManager.verify(cc_pair=test_cc_pair, user_performing_action=admin_user)

    # Verify that the curator can pause and unpause the CC pair
    CCPairManager.pause_cc_pair(cc_pair=test_cc_pair, user_performing_action=curator)

    # Verify that the curator can delete the CC pair
    CCPairManager.delete(cc_pair=test_cc_pair, user_performing_action=curator)
    CCPairManager.wait_for_deletion_completion(user_performing_action=curator)

    # Verify that the CC pair has been deleted
    CCPairManager.verify(
        cc_pair=test_cc_pair,
        verify_deleted=True,
        user_performing_action=admin_user,
    )
