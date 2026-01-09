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

    def _create_organisation(self, name="Org", description="Description", location="location"):
        admin = DataspaceUser.objects.create(
            email=f"{name.lower().replace(' ', '_')}@example.com"
        )
        return Organisation.objects.create(
            coverImageUrl="cover",
            logoUrl="logo",
            name=name,
            sector="sector",
            location=location,
            policyUrl="policy",
            description=description,
            admin=admin,
        )

    def _create_dda_template(self, organisation, record=None, tags=None):
        if record is None:
            record = {}
        if tags is None:
            tags = []
        return DataDisclosureAgreementTemplate.objects.create(
            version="1",
            templateId="tmpl-1",
            status="listed",
            organisationId=organisation,
            dataDisclosureAgreementRecord=record,
            dataDisclosureAgreementTemplateRevision={},
            dataDisclosureAgreementTemplateRevisionId="rev-1",
            tags=tags,
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
                "searchTags": "false",
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

    def test_search_by_dda_only_returns_matching_dda(self):
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
        self.assertEqual(len(orgs), 0)
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
        self.assertEqual(len(orgs), 0)
        self.assertEqual(len(ddas), 1)
        self.assertEqual(ddas[0]["organisationName"], org.name)

    def test_search_by_org_location_returns_matching_org(self):
        matching = self._create_organisation(name="Test Org", location="London")
        self._create_organisation(name="Other Org", location="Paris")

        response = self._get(
            {
                "search": "london",
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

    def test_search_by_org_description_matches(self):
        org = self._create_organisation(
            name="Test Org", description="This is a unique description"
        )

        response = self._get(
            {
                "search": "unique",
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
        self.assertEqual(orgs[0]["organisation"]["name"], org.name)

    def test_search_by_dda_dataset_no_longer_matches(self):
        org = self._create_organisation(name="Org One")
        self._create_dda_template(
            organisation=org,
            record={
                "purpose": "research",
                "description": "test description",
                "dataset": "vehicles",
            },
        )

        response = self._get(
            {
                "search": "vehicles",
                "searchOrgName": "false",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 0)

    def test_search_by_dda_purpose_and_description_still_works(self):
        org = self._create_organisation(name="Org One")
        self._create_dda_template(
            organisation=org,
            record={
                "purpose": "mobility research",
                "description": "transportation data analysis",
                "dataset": "vehicles",
            },
        )

        response = self._get(
            {
                "search": "mobility",
                "searchOrgName": "false",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 1)

        response = self._get(
            {
                "search": "transportation",
                "searchOrgName": "false",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "true",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 1)

    def test_search_org_name_does_not_return_matching_ddas(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={
                "purpose": "test purpose",
                "description": "test description",
                "dataset": "vehicles",
            },
        )

        response = self._get(
            {
                "search": "test",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        ddas = data.get("ddas", [])
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0]["organisation"]["name"], org.name)
        self.assertEqual(len(ddas), 0)

    def test_all_scopes_true_org_name_match_ddas_not_returned(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={
                "purpose": "different purpose",
                "description": "different description",
                "dataset": "vehicles",
            },
        )

        response = self._get(
            {
                "search": "test",
                "searchOrgName": "true",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "true",
                "searchTags": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        ddas = data.get("ddas", [])
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0]["organisation"]["name"], org.name)
        self.assertEqual(len(ddas), 0)

    def test_pagination_with_multiple_organisations(self):
        for i in range(15):
            self._create_organisation(name=f"Org {i}", location=f"Location {i}")

        response = self._get(
            {
                "search": "org",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "limit": "10",
                "offset": "0",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        pagination = data.get("organisationsPagination", {})
        self.assertEqual(len(orgs), 10)
        self.assertEqual(pagination.get("totalItems"), 15)
        self.assertEqual(pagination.get("limit"), 10)
        self.assertEqual(pagination.get("currentPage"), 1)
        self.assertEqual(pagination.get("totalPages"), 2)
        self.assertFalse(pagination.get("hasPrevious"))
        self.assertTrue(pagination.get("hasNext"))

        response = self._get(
            {
                "search": "org",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "limit": "10",
                "offset": "10",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        pagination = data.get("organisationsPagination", {})
        self.assertEqual(len(orgs), 5)
        self.assertEqual(pagination.get("totalItems"), 15)
        self.assertEqual(pagination.get("currentPage"), 2)
        self.assertTrue(pagination.get("hasPrevious"))
        self.assertFalse(pagination.get("hasNext"))

    def test_pagination_with_multiple_ddas(self):
        org = self._create_organisation(name="Test Org")
        for i in range(15):
            self._create_dda_template(
                organisation=org,
                record={
                    "purpose": f"test purpose {i}",
                    "description": f"test description {i}",
                    "dataset": "vehicles",
                },
            )

        response = self._get(
            {
                "search": "test",
                "searchOrgName": "false",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "false",
                "limit": "10",
                "offset": "0",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        pagination = data.get("ddasPagination", {})
        self.assertEqual(len(ddas), 10)
        self.assertEqual(pagination.get("totalItems"), 15)
        self.assertEqual(pagination.get("limit"), 10)
        self.assertEqual(pagination.get("currentPage"), 1)
        self.assertEqual(pagination.get("totalPages"), 2)
        self.assertFalse(pagination.get("hasPrevious"))
        self.assertTrue(pagination.get("hasNext"))

        response = self._get(
            {
                "search": "test",
                "searchOrgName": "false",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "false",
                "limit": "10",
                "offset": "10",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        pagination = data.get("ddasPagination", {})
        self.assertEqual(len(ddas), 5)
        self.assertEqual(pagination.get("totalItems"), 15)
        self.assertEqual(pagination.get("currentPage"), 2)
        self.assertTrue(pagination.get("hasPrevious"))
        self.assertFalse(pagination.get("hasNext"))

    def test_search_case_insensitive(self):
        org = self._create_organisation(name="Test Org", location="London", description="Test Description")
        response = self._get(
            {
                "search": "TEST",
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
        self.assertEqual(orgs[0]["organisation"]["name"], org.name)

    def test_search_with_special_characters(self):
        org = self._create_organisation(name="Test & Co", location="New York", description="Test's description")
        response = self._get(
            {
                "search": "&",
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

    def test_search_with_null_fields(self):
        org = self._create_organisation(name="Test Org", location="", description="")
        response = self._get(
            {
                "search": "test",
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

    def test_dda_with_null_record(self):
        org = self._create_organisation(name="Test Org")
        dda = DataDisclosureAgreementTemplate.objects.create(
            organisationId=org,
            status="listed",
            isLatestVersion=True,
            dataDisclosureAgreementRecord={"purpose": "test", "description": "test"},
        )
        response = self._get(
            {
                "search": "nonexistent",
                "searchOrgName": "false",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 0)

    def test_search_term_in_both_org_and_dda(self):
        org = self._create_organisation(name="Mobility Org")
        self._create_dda_template(
            organisation=org,
            record={
                "purpose": "mobility research",
                "description": "test",
            },
        )
        response = self._get(
            {
                "search": "mobility",
                "searchOrgName": "true",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        ddas = data.get("ddas", [])
        self.assertEqual(len(orgs), 1)
        self.assertEqual(len(ddas), 1)

    def test_search_term_only_in_dda_but_org_scope_only(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={
                "purpose": "mobility research",
                "description": "test",
            },
        )
        response = self._get(
            {
                "search": "mobility",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        ddas = data.get("ddas", [])
        self.assertEqual(len(orgs), 0)
        self.assertEqual(len(ddas), 0)

    def test_search_term_only_in_org_but_dda_scope_only(self):
        org = self._create_organisation(name="Mobility Org")
        response = self._get(
            {
                "search": "mobility",
                "searchOrgName": "false",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        ddas = data.get("ddas", [])
        self.assertEqual(len(orgs), 0)
        self.assertEqual(len(ddas), 0)

    def test_pagination_beyond_results(self):
        self._create_organisation(name="Test Org")
        response = self._get(
            {
                "search": "test",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "limit": "10",
                "offset": "100",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        pagination = data.get("organisationsPagination", {})
        self.assertEqual(len(orgs), 0)
        self.assertEqual(pagination.get("totalItems"), 1)
        self.assertEqual(pagination.get("currentPage"), 11)

    def test_pagination_with_zero_limit(self):
        for i in range(5):
            self._create_organisation(name=f"Org {i}")
        response = self._get(
            {
                "search": "org",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "limit": "0",
                "offset": "0",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        pagination = data.get("organisationsPagination", {})
        # Limit is normalized to minimum 1
        self.assertEqual(len(orgs), 1)
        self.assertEqual(pagination.get("limit"), 1)

    def test_pagination_with_negative_offset(self):
        self._create_organisation(name="Test Org")
        response = self._get(
            {
                "search": "test",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "limit": "10",
                "offset": "-5",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        # Should normalize negative offset to 0
        self.assertEqual(len(orgs), 1)

    def test_search_with_whitespace(self):
        org = self._create_organisation(name="Test Org")
        response = self._get(
            {
                "search": "   test   ",
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

    def test_tags_search_with_empty_tags(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={"purpose": "test", "description": "test"},
            tags=[],
        )
        response = self._get(
            {
                "search": "test",
                "searchOrgName": "false",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "searchTags": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 0)

    def test_tags_search_with_matching_tags(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={"purpose": "other", "description": "other"},
            tags=["mobility", "research"],
        )
        response = self._get(
            {
                "search": "mobility",
                "searchOrgName": "false",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "searchTags": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 1)

    def test_tags_search_case_insensitive(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={"purpose": "other", "description": "other"},
            tags=["Diabetes", "Healthcare"],
        )
        response = self._get(
            {
                "search": "diabetes",
                "searchOrgName": "false",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "searchTags": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 1)

    def test_tags_search_with_all_scopes(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={"purpose": "other", "description": "other"},
            tags=["diabetes", "research"],
        )
        response = self._get(
            {
                "search": "diabetes",
                "searchOrgName": "true",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "false",
                "searchTags": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 1)

    def test_tags_search_partial_match(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={"purpose": "other", "description": "other"},
            tags=["healthcare", "medical-research"],
        )
        response = self._get(
            {
                "search": "health",
                "searchOrgName": "false",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "searchTags": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 1)

    def test_tags_search_with_special_characters(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={"purpose": "other", "description": "other"},
            tags=["e-health", "data-science"],
        )
        response = self._get(
            {
                "search": "e-health",
                "searchOrgName": "false",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "searchTags": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 1)

    def test_tags_search_multiple_ddas(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={"purpose": "other", "description": "other"},
            tags=["diabetes", "healthcare"],
        )
        self._create_dda_template(
            organisation=org,
            record={"purpose": "other", "description": "other"},
            tags=["diabetes", "research"],
        )
        self._create_dda_template(
            organisation=org,
            record={"purpose": "other", "description": "other"},
            tags=["mobility", "research"],
        )
        response = self._get(
            {
                "search": "diabetes",
                "searchOrgName": "false",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "searchTags": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 2)

    def test_tags_search_no_match(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={"purpose": "other", "description": "other"},
            tags=["mobility", "research"],
        )
        response = self._get(
            {
                "search": "diabetes",
                "searchOrgName": "false",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
                "searchTags": "true",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 0)

    def test_multiple_organisations_same_name_distinct(self):
        admin1 = DataspaceUser.objects.create(email="admin1@example.com")
        admin2 = DataspaceUser.objects.create(email="admin2@example.com")
        org1 = Organisation.objects.create(
            coverImageUrl="cover",
            logoUrl="logo",
            name="Same Name",
            sector="sector",
            location="Location 1",
            policyUrl="policy",
            description="Description 1",
            admin=admin1,
        )
        org2 = Organisation.objects.create(
            coverImageUrl="cover",
            logoUrl="logo",
            name="Same Name",
            sector="sector",
            location="Location 2",
            policyUrl="policy",
            description="Description 2",
            admin=admin2,
        )
        response = self._get(
            {
                "search": "same",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        self.assertEqual(len(orgs), 2)
        org_names = [org["organisation"]["name"] for org in orgs]
        self.assertEqual(org_names.count("Same Name"), 2)

    def test_very_long_search_term(self):
        org = self._create_organisation(name="Test Org")
        long_search = "a" * 1000
        response = self._get(
            {
                "search": long_search,
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        self.assertEqual(len(orgs), 0)

    def test_search_with_unicode_characters(self):
        org = self._create_organisation(name="Test Org", description="Test with émojis 🚀 and spëcial çhars")
        response = self._get(
            {
                "search": "émojis",
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

    def test_sort_by_org_name_with_dda_scope_only(self):
        org = self._create_organisation(name="Test Org")
        self._create_dda_template(
            organisation=org,
            record={"purpose": "test", "description": "test"},
        )
        response = self._get(
            {
                "search": "test",
                "searchOrgName": "false",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "false",
                "sortBy": "orgName",
                "sortOrder": "asc",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ddas = data.get("ddas", [])
        self.assertEqual(len(ddas), 1)

    def test_search_returns_empty_when_no_matches(self):
        self._create_organisation(name="Test Org")
        response = self._get(
            {
                "search": "nonexistent",
                "searchOrgName": "true",
                "searchDdaPurpose": "true",
                "searchDdaDescription": "true",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        ddas = data.get("ddas", [])
        self.assertEqual(len(orgs), 0)
        self.assertEqual(len(ddas), 0)

    def test_search_with_production_like_data(self):
        """Test search with real demo production organisation data"""
        # Create organisations similar to demo production data
        production_orgs = [
            {"name": "Data Analysis AB", "location": "Sweden", "description": "For queries about how we are managing your data please contact the Data Protection Officer", "sector": "Scientific research and development"},
            {"name": "Dexcom", "location": "Sweden", "description": "For queries about how we are managing your data please contact the Data Protection Officer", "sector": "Healthcare"},
            {"name": "Medtronic", "location": "Sweden", "description": "For queries about how we are managing your data please contact the Data Protection Officer", "sector": "Healthcare"},
            {"name": "Nordic Health Innovation", "location": "Sweden", "description": "For queries about how we are managing your data please contact the Data Protection Officer.", "sector": "Healthcare"},
            {"name": "Hamling IT AB", "location": "Sweden", "description": "Consultancy and Medical Device reseller in the Nordics.", "sector": "Scientific research and development"},
            {"name": "Data4Diabetes", "location": "Sweden", "description": "For queries about how we are managing your data please contact the Data Protection Officer.", "sector": "Healthcare"},
            {"name": "Tellu AS", "location": "Norway", "description": "Tellu AS is a Norwegian software and technology company that delivers cloud-based IoT and eHealth solutions.", "sector": "Healthcare"},
            {"name": "ECG247", "location": "Norway", "description": "ECG247 is a medically certified sensor for continuous long-term monitoring of the heart rhythm for assessment of heart rhythm disorders.", "sector": "Healthcare"},
        ]

        for org_data in production_orgs:
            self._create_organisation(
                name=org_data["name"],
                location=org_data["location"],
                description=org_data["description"]
            )

        # Test search by organisation name
        response = self._get(
            {
                "search": "Dexcom",
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
        self.assertEqual(orgs[0]["organisation"]["name"], "Dexcom")

        # Test search by location (Sweden)
        response = self._get(
            {
                "search": "Sweden",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        self.assertEqual(len(orgs), 6)

        # Test search by location (Norway)
        response = self._get(
            {
                "search": "Norway",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        self.assertEqual(len(orgs), 2)

        # Test search by description term
        response = self._get(
            {
                "search": "Data Protection Officer",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        self.assertEqual(len(orgs), 5)

        # Test search by partial name
        response = self._get(
            {
                "search": "Health",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        org_names = [org["organisation"]["name"] for org in orgs]
        self.assertIn("Nordic Health Innovation", org_names)
        self.assertIn("Tellu AS", org_names)  # Contains "Health" in description

        # Test search with no matches
        response = self._get(
            {
                "search": "NonExistentOrg",
                "searchOrgName": "true",
                "searchDdaPurpose": "false",
                "searchDdaDescription": "false",
                "searchDataset": "false",
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        orgs = data.get("organisations", [])
        self.assertEqual(len(orgs), 0)
