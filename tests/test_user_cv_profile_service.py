from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.auth.models import (
    CurrentUser,
    Role,
)
from src.auth.user_context import (
    UserContext,
)
from src.career.user_cv_profile_service import (
    UserCVProfileService,
)
from src.profile import Profile


class TestUserCVProfileService(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.storage_root = (
            Path(
                self.temporary_directory.name
            )
            / "users"
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_context(
        self,
        user_id: str,
        email: str,
        authenticated: bool = True,
        authorized: bool = True,
    ) -> UserContext:
        return UserContext(
            current_user=CurrentUser(
                user_id=user_id,
                subject=f"subject-{user_id}",
                email=email,
                display_name=user_id,
                authenticated=authenticated,
                authorized=authorized,
                roles=(
                    Role.USER,
                ),
            )
        )

    def create_service(
        self,
        user_id: str,
        email: str,
    ) -> UserCVProfileService:
        return UserCVProfileService(
            user_context=self.create_context(
                user_id=user_id,
                email=email,
            ),
            storage_root=self.storage_root,
        )

    def create_profile(
        self,
        name: str = "DSI / CIO",
    ) -> Profile:
        return Profile(
            name=name,
            keywords=[
                "gouvernance si",
                "transformation si",
                "cobit",
            ],
            locations=[
                "Paris",
            ],
            salary_min=0,
            remote=True,
        )

    def test_profiles_directory_is_user_scoped(
        self,
    ):
        service = self.create_service(
            user_id="user-123",
            email="first@example.com",
        )

        self.assertEqual(
            service.profiles_directory,
            (
                self.storage_root.resolve()
                / "user-123"
                / "profiles"
            ),
        )

    def test_user_directories_are_created(
        self,
    ):
        service = self.create_service(
            user_id="user-123",
            email="first@example.com",
        )

        self.assertTrue(
            service.profiles_directory.is_dir()
        )

        self.assertTrue(
            service.storage_paths
            .cvs_directory
            .is_dir()
        )

    def test_two_users_have_different_profile_roots(
        self,
    ):
        first = self.create_service(
            user_id="user-123",
            email="first@example.com",
        )

        second = self.create_service(
            user_id="user-456",
            email="second@example.com",
        )

        self.assertNotEqual(
            first.profiles_directory,
            second.profiles_directory,
        )

    def test_two_users_can_create_same_profile_slug(
        self,
    ):
        first = self.create_service(
            user_id="user-123",
            email="first@example.com",
        )

        second = self.create_service(
            user_id="user-456",
            email="second@example.com",
        )

        first_result = first.create_profile(
            profile=self.create_profile()
        )

        second_result = second.create_profile(
            profile=self.create_profile()
        )

        self.assertEqual(
            first_result.profile_id,
            second_result.profile_id,
        )

        self.assertNotEqual(
            first_result.config_path,
            second_result.config_path,
        )

        self.assertTrue(
            first_result.config_path.is_file()
        )

        self.assertTrue(
            second_result.config_path.is_file()
        )

    def test_user_lists_only_own_profiles(
        self,
    ):
        first = self.create_service(
            user_id="user-123",
            email="first@example.com",
        )

        second = self.create_service(
            user_id="user-456",
            email="second@example.com",
        )

        first.create_profile(
            profile=self.create_profile(
                "DSI / CIO"
            )
        )

        second.create_profile(
            profile=self.create_profile(
                "Data Engineer"
            )
        )

        first_profiles = set(
            first.list_profiles()
        )

        second_profiles = set(
            second.list_profiles()
        )

        self.assertIn(
            "dsi_cio",
            first_profiles,
        )

        self.assertNotIn(
            "data_engineer",
            first_profiles,
        )

        self.assertIn(
            "data_engineer",
            second_profiles,
        )

        self.assertNotIn(
            "dsi_cio",
            second_profiles,
        )

    def test_user_cannot_load_other_user_profile(
        self,
    ):
        first = self.create_service(
            user_id="user-123",
            email="first@example.com",
        )

        second = self.create_service(
            user_id="user-456",
            email="second@example.com",
        )

        second.create_profile(
            profile=self.create_profile(
                "Data Engineer"
            )
        )

        with self.assertRaises(
            (
                FileNotFoundError,
                ValueError,
                KeyError,
            )
        ):
            first.load_profile_config(
                "data_engineer"
            )

    def test_unauthorized_context_is_rejected(
        self,
    ):
        context = self.create_context(
            user_id="user-123",
            email="first@example.com",
            authenticated=True,
            authorized=False,
        )

        with self.assertRaises(
            Exception
        ):
            UserCVProfileService(
                user_context=context,
                storage_root=self.storage_root,
            )

    def test_unauthenticated_context_is_rejected(
        self,
    ):
        context = self.create_context(
            user_id="user-123",
            email="first@example.com",
            authenticated=False,
            authorized=False,
        )

        with self.assertRaises(
            Exception
        ):
            UserCVProfileService(
                user_context=context,
                storage_root=self.storage_root,
            )

    def test_invalid_context_type_is_rejected(
        self,
    ):
        with self.assertRaises(
            TypeError
        ):
            UserCVProfileService(
                user_context=object(),
                storage_root=self.storage_root,
            )

    def test_owned_profile_path_is_accepted(
        self,
    ):
        service = self.create_service(
            user_id="user-123",
            email="first@example.com",
        )

        profile_path = (
            service.storage_paths
            .profile_directory(
                "dsi_cio"
            )
        )

        self.assertEqual(
            service.assert_profile_path_owned(
                profile_path
            ),
            profile_path.resolve(),
        )

    def test_cv_path_is_not_accepted_as_profile_path(
        self,
    ):
        service = self.create_service(
            user_id="user-123",
            email="first@example.com",
        )

        with self.assertRaises(
            ValueError
        ):
            service.assert_profile_path_owned(
                service.storage_paths
                .cvs_directory
            )


if __name__ == "__main__":
    unittest.main()