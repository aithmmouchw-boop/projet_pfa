from types import SimpleNamespace

from django.test import SimpleTestCase

from clinic_common.admin_permissions import ClinicDeletePermissionMixin
from clinic_common.visual_assets import medecin_photo_url, named_doctor_photo_url


class VisualAssetsTests(SimpleTestCase):
    def test_named_doctor_photo_uses_female_portrait_for_wafae(self):
        self.assertIn("33055499", named_doctor_photo_url("Dr. Wafae Ait Hmmouch"))

    def test_named_doctor_photo_uses_female_portrait_for_chaimaa(self):
        self.assertIn("32254665", named_doctor_photo_url("Dr. Chaimaa Elgharzaoui"))

    def test_medecin_photo_url_prefers_named_portrait(self):
        user = SimpleNamespace(
            email="ceour@aesculia.local",
            get_full_name=lambda: "wafae ceour",
        )
        medecin = SimpleNamespace(user=user, specialite="Cardiologie", photo=None)

        self.assertIn("33055499", medecin_photo_url(medecin))


class ClinicDeletePermissionMixinTests(SimpleTestCase):
    def test_admin_role_can_delete_cascaded_objects(self):
        class BaseAdmin:
            def has_delete_permission(self, request, obj=None):
                return False

        class Admin(ClinicDeletePermissionMixin, BaseAdmin):
            pass

        request = SimpleNamespace(
            user=SimpleNamespace(is_superuser=False, is_staff=True, role="admin")
        )

        self.assertTrue(Admin().has_delete_permission(request))
