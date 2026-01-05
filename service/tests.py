import json

from django.test import TestCase
from django.urls import reverse

from data_disclosure_agreement.models import DataDisclosureAgreementTemplate
from onboard.models import DataspaceUser
from organisation.models import Organisation

# Create your tests here.


class SearchViewTests(TestCase):
    def setUp(self):
        pass

    def _create_organisation(self, name="Org", description="Description"):
        admin = DataspaceUser.objects.create(
            email=f"{name.lower().replace(' ', '_')}@example.com"
        )
        return Organisation.objects.create(
            coverImageUrl="cover",
            logoUrl="logo",
            name=name,
            sector="sector",
            location="location",
            policyUrl="policy",
            description=description,
            admin=admin,
        )

    def _create_dda_template(self, organisation, record):
        return DataDisclosureAgreementTemplate.objects.create(
            version="1",
            templateId="tmpl-1",
            status="listed",
            organisationId=organisation,
            dataDisclosureAgreementRecord=record,
            dataDisclosureAgreementTemplateRevision={},
            dataDisclosureAgreementTemplateRevisionId="rev-1",
        )

    def _get(self, params):
        url = reverse("search")
        return self.client.get(url, params)

    def test_missing_search_returns_invalid_request(self):
        response = self._get({})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data.get("error"), "invalid_request")
        self.assertIn("search parameter is required", data.get("error_description", ""))

    def test_all_scopes_false_returns_invalid_request(self):
        response = self._get(
            {
                "search": "foo",
                "searchOrgName": "false",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data.get("error"), "invalid_request")
        self.assertIn(
            "At least one search scope must be true", data.get("error_description", "")
        )

    def test_invalid_boolean_value_returns_invalid_request(self):
        response = self._get({"search": "foo", "searchOrgName": "maybe"})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data.get("error"), "invalid_request")
        self.assertIn("searchOrgName", data.get("error_description", ""))

    def test_search_by_org_name_only_returns_matching_org(self):
        matching = self._create_organisation(name="Alpha Hospital")
        self._create_organisation(name="Beta Clinic")

        response = self._get(
            {
                "search": "hospital",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0]["organisation"]["name"], matching.name)
        self.assertEqual(data.get("ddas"), [])

    def test_search_by_dda_only_returns_matching_org_and_dda(self):
        org = self._create_organisation(name="Org One")
        self._create_dda_template(
            organisation=org,
            record={
                "purpose": "mobility research",
                "description": "test",
                "dataset": "vehicles",
            },
        )

        response = self._get(
            {
                "search": "mobility",
                "searchOrgName": "false",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        ddas = data.get("ddas", [])
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0]["organisation"]["name"], org.name)
        self.assertEqual(len(ddas), 1)
        self.assertEqual(ddas[0]["organisationName"], org.name)

    def test_all_scopes_true_org_and_dda_match(self):
        org = self._create_organisation(name="Mobility Org")
        self._create_dda_template(
            organisation=org,
            record={
                "purpose": "mobility research",
                "description": "something",
            },
        )

        response = self._get(
            {
                "search": "mobility",
                "searchOrgName": "true",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        ddas = data.get("ddas", [])
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0]["organisation"]["name"], org.name)
        self.assertEqual(len(ddas), 1)
        self.assertEqual(ddas[0]["organisationName"], org.name)

    def test_all_scopes_true_org_match_no_dda(self):
        org = self._create_organisation(name="Mobility Org")
        # No DDA created, so only organisation name can match

        response = self._get(
            {
                "search": "mobility",
                "searchOrgName": "true",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        ddas = data.get("ddas", [])
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0]["organisation"]["name"], org.name)
        self.assertEqual(len(ddas), 0)

    def test_all_scopes_true_dda_match_org_name_not_matching(self):
        org = self._create_organisation(name="Org X")
        self._create_dda_template(
            organisation=org,
            record={
                "purpose": "mobility research",
                "description": "something",
            },
        )

        response = self._get(
            {
                "search": "mobility",
                "searchOrgName": "true",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        ddas = data.get("ddas", [])
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0]["organisation"]["name"], org.name)
        self.assertEqual(len(ddas), 1)
        self.assertEqual(ddas[0]["organisationName"], org.name)
