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


def test_get_morpheme_by_timestamp(client):
    response = client.get(
        BASE_PATH + "by_episode/1/?timestamp=00:00:01",
    )
    assert response.status_code == 200
    assert len(response.get_json()["morphemes"]) == 1


def test_get_morpheme_by_timestamp_not_found(client):
    response = client.get(
        BASE_PATH + "by_episode/1/?timestamp=00:00:00",
    )
    assert response.status_code == 404
    assert response.get_json()["message"] == "Morpheme not found"


def test_get_morpheme_by_timestamp_invalid_timestamp(client):
    response = client.get(
        BASE_PATH + "by_episode/1/?timestamp=99:99:99",
    )
    assert response.status_code == 400
    assert response.get_json()["message"].startswith("Invalid timestamp")


def test_post_morpheme(client):
    response = client.post(
        BASE_PATH + "by_episode/1/",
        json={
            "timestamp": "23:59:59",
            "speaker": "A",
            "token": "test",
        }
    )
    assert response.status_code == 201
    assert response.get_json() == {
        "message": "Morpheme created"
    }


def test_post_morpheme_already_exists(client):
    response = client.post(
        BASE_PATH + "by_episode/1/",
        json={
            "timestamp": "00:00:01",
            "speaker": "A",
            "token": "test",
        }
    )

    assert response.get_json() == {
        "message": "Morpheme already exists"
    }
    assert response.status_code == 403


invalid_post_body = [
    {"speaker": "A", "token": "test"},  # no timestamp
    {"timestamp": "00:00:00", "token": "test"},  # no speaker
    {"timestamp": "00:00:00", "speaker": "A"},  # no token
    {"timestamp": "00:00", "speaker": "A", "token": "test"},  # invalid timestamp
    {"timestamp": "00:00:00", "speaker": "", "token": "test"},  # invalid speaker
    {"timestamp": "00:00:00", "speaker": "A", "token": ""},  # invalid token
]


def test_post_morpheme_invalid_body(client):
    for body in invalid_post_body:
        response = client.post(
            BASE_PATH + "by_episode/1/",
            json=body
        )
        assert "Invalid request body" in response.get_json()["message"]
        assert response.status_code == 400


def test_put_morpheme(client):
    response = client.put(
        BASE_PATH + "by_episode/1/",
        json={
            "timestamp": "00:00:01",
            "speaker": "B",
            "token": "test",
        }
    )
    assert response.get_json() == {
        "message": "Morpheme updated"
    }
    assert response.status_code == 201


def test_put_morpheme_invalid_body(client):
    for body in invalid_post_body:
        response = client.put(
            BASE_PATH + "by_episode/1/",
            json=body
        )
        assert "Invalid request body" in response.get_json()["message"]
        assert response.status_code == 400


def test_delete_morpheme(client):
    response = client.delete(
        BASE_PATH + "by_episode/1/?timestamp=00:00:02",
    )
    assert response.get_json() == {
        "message": "Morpheme deleted"
    }
    assert response.status_code == 202


def test_delete_morpheme_not_found(client):
    response = client.delete(
        BASE_PATH + "by_episode/1/?timestamp=00:00:03",
    )
    assert response.get_json() == {
        "message": "Morpheme not found"
    }
    assert response.status_code == 404
