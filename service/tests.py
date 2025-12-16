from django.test import TestCase
from django.urls import reverse
import json
from onboard.models import DataspaceUser
from organisation.models import Organisation
from data_disclosure_agreement.models import DataDisclosureAgreementTemplate

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

    def _assert_success_response(
        self,
        data,
        *,
        query,
        searchOrgName,
        searchDdaPurpose,
        searchDdaDescription,
        searchDataset,
    ):
        self.assertIn("dataDisclosureAgreements", data)
        self.assertIn("pagination", data)
        self.assertIn("searchMeta", data)
        self.assertIsInstance(data.get("dataDisclosureAgreements"), list)

        pagination = data.get("pagination")
        self.assertIn("currentPage", pagination)
        self.assertIn("totalItems", pagination)
        self.assertIn("totalPages", pagination)
        self.assertIn("limit", pagination)
        self.assertIn("hasPrevious", pagination)
        self.assertIn("hasNext", pagination)

        search_meta = data.get("searchMeta")
        self.assertEqual(search_meta.get("query"), query)
        self.assertEqual(search_meta.get("searchOrgName"), searchOrgName)
        self.assertEqual(search_meta.get("searchDdaPurpose"), searchDdaPurpose)
        self.assertEqual(
            search_meta.get("searchDdaDescription"), searchDdaDescription
        )
        self.assertEqual(search_meta.get("searchDataset"), searchDataset)

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
        other = self._create_organisation(name="Beta Clinic")

        self._create_dda_template(
            organisation=matching,
            record={
                "purpose": "test",
                "description": "test",
                "dataset": "test",
            },
        )
        self._create_dda_template(
            organisation=other,
            record={
                "purpose": "test",
                "description": "test",
                "dataset": "test",
            },
        )

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
        self.assertNotIn("organisations", data)
        self._assert_success_response(
            data,
            query="hospital",
            searchOrgName=True,
            searchDdaPurpose=False,
            searchDdaDescription=False,
            searchDataset=False,
        )
        ddas = data.get("dataDisclosureAgreements", [])
        self.assertEqual(len(ddas), 1)
        self.assertEqual(ddas[0]["organisationName"], matching.name)

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
        ddas = data.get("dataDisclosureAgreements", [])
        self.assertNotIn("organisations", data)
        self._assert_success_response(
            data,
            query="mobility",
            searchOrgName=False,
            searchDdaPurpose=True,
            searchDdaDescription=True,
            searchDataset=True,
        )
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
        ddas = data.get("dataDisclosureAgreements", [])
        self.assertNotIn("organisations", data)
        self._assert_success_response(
            data,
            query="mobility",
            searchOrgName=True,
            searchDdaPurpose=True,
            searchDdaDescription=True,
            searchDataset=True,
        )
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
        ddas = data.get("dataDisclosureAgreements", [])
        self.assertNotIn("organisations", data)
        self._assert_success_response(
            data,
            query="mobility",
            searchOrgName=True,
            searchDdaPurpose=True,
            searchDdaDescription=True,
            searchDataset=True,
        )
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
        ddas = data.get("dataDisclosureAgreements", [])
        self.assertNotIn("organisations", data)
        self._assert_success_response(
            data,
            query="mobility",
            searchOrgName=True,
            searchDdaPurpose=True,
            searchDdaDescription=True,
            searchDataset=True,
        )
        self.assertEqual(len(ddas), 1)
        self.assertEqual(ddas[0]["organisationName"], org.name)
