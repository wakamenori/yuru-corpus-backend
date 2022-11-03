BASE_PATH = "/dev/summary/"


def test_get_summary(client):
    response = client.get(
        BASE_PATH,
    )
    assert response.status_code == 200
    assert len(response.get_json()["summary"]) > 0


def test_get_summary_by_id(client):
    response = client.get(
        BASE_PATH + "by_episode/1/",
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "id": 1,
        "publicationDate": "2021-03-11",
        "thumbnailUrl": "https://i.ytimg.com/vi/2YY9DT4uDh0/sddefault.jpg",
        "title": "「イルカも喋る」は大ウソ【言語学って何？】#1",
        "videoUrl": "https://www.youtube.com/watch?v=2YY9DT4uDh0",
        "isAnalyzed": True,
        "channel": "ゆる言語学ラジオ",
    }


def test_get_summary_by_id_404(client):
    response = client.get(
        BASE_PATH + "by_episode/999999999999999999/",
    )
    assert response.status_code == 404
    assert response.get_json()["message"] == "Episode not found"
