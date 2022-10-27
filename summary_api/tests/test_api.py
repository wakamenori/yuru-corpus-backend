BASE_PATH = "/dev/summary/"


def test_get_summary(client):
    response = client.get(
        BASE_PATH,
    )
    assert response.status_code == 200
    assert len(response.get_json()["summary"]) > 0
