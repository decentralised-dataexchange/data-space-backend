from django.test import TestCase
from rest_framework.test import APIClient

# Create your tests here.


class NonGetAppendSlashMiddlewareTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _assert_same_response(self, method: str, path: str, **kwargs):
        client_method = getattr(self.client, method)

        base_path = path
        if base_path.endswith("/"):
            alt_path = base_path.rstrip("/")
            if not alt_path:
                alt_path = base_path
        else:
            alt_path = base_path + "/"

        response_base = client_method(base_path, **kwargs)
        response_alt = client_method(alt_path, **kwargs)

        msg_prefix = f"{method.upper()} {base_path} vs {alt_path}: "

        self.assertNotEqual(
            response_base.status_code,
            500,
            msg_prefix
            + f"unexpected 500 for base path; body={response_base.content!r}",
        )
        self.assertEqual(
            response_base.status_code,
            response_alt.status_code,
            msg_prefix + "status mismatch: "
            f"base={response_base.status_code}, "
            f"alt={response_alt.status_code}, "
            f"base_body={response_base.content!r}, "
            f"alt_body={response_alt.content!r}",
        )
        self.assertEqual(
            response_base.content,
            response_alt.content,
            msg_prefix + "body mismatch: "
            f"base_body={response_base.content!r}, "
            f"alt_body={response_alt.content!r}",
        )

    def test_put_dda_status_with_and_without_trailing_slash_behave_the_same(self):
        base_path = "/config/data-disclosure-agreement/test-id/status"
        data = {"status": "listed"}

        self._assert_same_response("put", base_path, data=data, format="json")

    def test_post_service_token_with_and_without_trailing_slash_behave_the_same(self):
        base_path = "/service/token"
        data = {"grant_type": "client_credentials"}

        self._assert_same_response("post", base_path, data=data)

    def test_non_existing_path_behaves_consistently_for_non_get(self):
        base_path = "/non-existing-endpoint-for-middleware-test"

        self._assert_same_response("put", base_path)
