from urllib.parse import parse_qs, urlsplit

from django.test import SimpleTestCase

from patients.views import _normalise_slot_iso, _rdv_booking_url


class RdvBookingUrlTests(SimpleTestCase):
    def test_booking_url_encodes_timezone_plus(self):
        slot = "2026-05-18T09:00:00+00:00"

        url = _rdv_booking_url(1, slot)
        query = parse_qs(urlsplit(url).query)

        self.assertEqual(query["medecin"], ["1"])
        self.assertEqual(query["slot"], [slot])

    def test_slot_normalisation_repairs_space_offset(self):
        self.assertEqual(
            _normalise_slot_iso("2026-05-18T09:00:00 00:00"),
            "2026-05-18T09:00:00+00:00",
        )
