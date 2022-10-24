BASE_PATH = "/dev/hello/"


def test_hello(client):
    response = client.get(
        BASE_PATH,
    )
    assert response.status_code == 200
