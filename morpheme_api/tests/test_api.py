BASE_PATH = "/dev/morpheme/"


def test_get_morpheme(client):
    response = client.get(
        BASE_PATH + "by_episode/1/",
    )
    assert response.status_code == 200
    assert len(response.get_json()["morphemes"]) > 0


def test_get_morpheme_not_found(client):
    response = client.get(
        BASE_PATH + "by_episode/0/",
    )
    assert response.status_code == 404
    assert response.get_json() == {
        "message": "Morpheme not found"
    }
