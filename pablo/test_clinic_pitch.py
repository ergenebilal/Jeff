"""Guards for first-contact outreach text: it may only say things that are true today.
CyberGene has no past clinic work to cite, no measured statistics, and makes no speed promises."""
import re
import unittest
import urllib.parse

from clinic_lead_hunter import ClinicLeadHunter as H

FORBIDDEN = [
    (r'%\s*\d|\d\s*%', 'percentage statistics'),
    (r'\d+\s*(saniye|dakikada|dk)', 'speed promises'),
    (r'gözlemlediğimiz|çalışmalarımızda|çalışmalarda|müşterilerimiz|referans|vaka', 'invented past work'),
    (r'\b(Jeff|Pablo|Guardian)\b', 'internal code names'),
    (r'cybergene\.com\.tr', 'wrong domain'),
    (r'garanti|kesin sonuç|risksiz', 'guarantees'),
]


class PitchHonestyTests(unittest.TestCase):
    def all_texts(self):
        texts = []
        for niche in H.NICHE_CATEGORIES:
            pitch = H.generate_clinic_pitch('Örnek Klinik', niche, instagram_handle='ornek')
            texts += [pitch['subject'], pitch['body'], pitch['value_prop']]
        return texts

    def test_no_unverifiable_claims_anywhere_in_generated_text(self):
        for text in self.all_texts():
            text = re.sub(r'https?://\S+', '', text)   # URL percent-encoding (%C3%BC) is not a statistic
            for pattern, why in FORBIDDEN:
                self.assertIsNone(re.search(pattern, text, re.I), f'{why}: {text[:80]!r}')

    def test_says_it_is_a_sample_and_final_decision_stays_with_the_owner(self):
        body = H.generate_clinic_pitch('Örnek Klinik', 'dental')['body']
        self.assertIn('temsili', body)
        self.assertIn('Son karar her zaman sizde', body)
        self.assertIn('yok sayabilirsiniz', body)      # easy way out

    def test_uses_the_real_domain(self):
        self.assertIn('https://cybergene.co', H.generate_clinic_pitch('X', 'dental')['body'])

    def test_contact_person_replaces_company_greeting(self):
        body = H.generate_clinic_pitch('Klinik', 'dental', contact_person='Dr. Ayşe')['body']
        self.assertTrue(body.startswith('Merhaba Dr. Ayşe,'))


class ShowroomLinkTests(unittest.TestCase):
    def params(self, url):
        return urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)

    def test_link_points_to_showroom_with_name_and_question(self):
        url = H.showroom_link('Dr. Ahmet', 'Gece mesajlara yetişemiyoruz')
        self.assertTrue(url.startswith('https://cybergene.co/showroom/?'))
        q = self.params(url)
        self.assertEqual(q['for'], ['Dr. Ahmet'])
        self.assertEqual(q['soru'], ['Gece mesajlara yetişemiyoruz'])

    def test_limits_match_the_site(self):
        q = self.params(H.showroom_link('A' * 80, 'b' * 500))
        self.assertLessEqual(len(q['for'][0]), 40)
        self.assertLessEqual(len(q['soru'][0]), 300)

    def test_markup_and_odd_characters_are_stripped_from_the_name(self):
        name = self.params(H.showroom_link('<script>alert(1)</script> Klinik', 'x'))['for'][0]
        self.assertNotIn('<', name)
        self.assertNotIn('>', name)
        self.assertNotIn('(', name)

    def test_default_question_is_used_when_none_given(self):
        self.assertEqual(self.params(H.showroom_link('X'))['soru'], [H.DEFAULT_QUESTION])


class SeedHonestyTests(unittest.TestCase):
    def test_seeds_are_not_labelled_verified_without_verification(self):
        import inspect
        source = inspect.getsource(H.seed_initial_verified_clinics)
        self.assertNotIn('fact_check_status="VERIFIED"', source)

    def test_unverified_seed_clinics_never_enter_the_pipeline(self):
        # Two of the four seed domains do not exist and two contact records could not be confirmed.
        self.assertEqual(H.seed_initial_verified_clinics(), [])


if __name__ == '__main__':
    unittest.main()
