"""API v2 tests."""
from kilink.backend import kilinkbackend, KilinkDataTooBigError
from kilink.config import config, UNITTESTING_ENVIRONMENT_VALUE
from kilink.main import app

config.load_config(UNITTESTING_ENVIRONMENT_VALUE)

test_client = app.test_client()


class TestCreateLinkode:
    EXPECTED_KEYS_IN_RESPONSE = [
        "linkode_id",
        "linkode_url",
        "root_id",
        "root_url",
    ]

    def test_creates_new_root_with_all_params(self):
        payload = {
            "content": "print('hello world')",
            "text_type": "python",
        }
        response = test_client.post("/api/2/linkode/", json=payload)

        for key in self.EXPECTED_KEYS_IN_RESPONSE:
            assert key in response.json

        assert response.status_code == 201

        # created linkode is the root of its tree
        assert response.json["linkode_id"] == response.json["root_id"]

    def test_creates_new_root_without_text_type(self):
        payload = {
            "content": "print('hello world')",
        }
        response = test_client.post("/api/2/linkode/", json=payload)

        for key in self.EXPECTED_KEYS_IN_RESPONSE:
            assert key in response.json

        assert response.status_code == 201

    def test_creates_new_revision(self):
        parent_id = kilinkbackend.create_linkode(content="", text_type="").linkode_id

        payload = {
            "content": "print('hello world')",
            "text_type": "python",
        }
        response = test_client.post(f"/api/2/linkode/{parent_id}/", json=payload)

        for key in self.EXPECTED_KEYS_IN_RESPONSE:
            assert key in response.json

        assert response.status_code == 201

        # new linkoded created with id different than its parent
        assert response.json["linkode_id"] != parent_id
        assert response.json["root_id"] == parent_id

    def test_creates_new_revision_when_parent_not_found(self):
        response = test_client.post(
            "/api/2/linkode/someNonExistingLinkodeId/", json={"content": "x"}
        )

        assert response.status_code == 404

    def test_creates_linkode_without_content_returns_bad_request(self):
        response = test_client.post("/api/2/linkode/", json={})

        assert response.status_code == 400

    def test_creates_linkode_when_content_too_long(self, mocker):
        mocker.patch(
            "kilink.views_v2.kilinkbackend.create_linkode",
            side_effect=KilinkDataTooBigError
        )
        response = test_client.post("/api/2/linkode/", json={"content": "x"})

        assert response.status_code == 413
        assert "too big" in str(response.data)


class TestGetLinkode:
    def test_get_linkode_happy_path(self):
        linkode = kilinkbackend.create_linkode(content="print('hello world')", text_type="python")

        response = test_client.get(f"/api/2/linkode/{linkode.linkode_id}")

        assert response.status_code == 200
        assert response.json["content"] == "print('hello world')"
        assert response.json["text_type"] == "python"
        assert response.json["linkode_id"] == linkode.linkode_id
        assert response.json["root_id"] == linkode.root
        assert "timestamp" in response.json
        assert "linkode_url" in response.json
        assert "root_id" in response.json

    def test_get_linkode_when_not_found(self):
        response = test_client.get("/api/2/linkode/SomeUnexistingId/")

        assert response.status_code == 404
