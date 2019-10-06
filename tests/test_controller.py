

def test_health_endpoint_returns_200(flask_test_client):

    response = flask_test_client.get('/health')
    assert response.status_code == 200


def test_actions_endpoint_returns_200(flask_test_client):

    response = flask_test_client.get('/Relays/1/On')
    assert response.status_code == 200

    response = flask_test_client.get('/Relays/1/timer')
    assert response.status_code == 200

    response = flask_test_client.get('/Relays/1/Off')
    assert response.status_code == 200

    response = flask_test_client.get('/Relays/1/Off')
    assert response.status_code == 200

    response = flask_test_client.get('/Relays/2/auto')
    assert response.status_code == 200


def test_timer_endpoint_returns_200(flask_test_client):

    response = flask_test_client.get('/timer/Relay/3')
    assert response.status_code == 200


def test_auto_endpoint_returns_200(flask_test_client):

    response = flask_test_client.get('/auto/Relay/2')
    assert response.status_code == 200


def test_set_timer_endpoint_returns_200(flask_test_client):  # TODO test POST form

    response = flask_test_client.get('/set_timer')
    assert response.status_code == 200


def test_set_auto_endpoint_returns_200(flask_test_client):  # TODO test POST form

    response = flask_test_client.get('/set_auto')
    assert response.status_code == 200
