import base64


def test_health_endpoint_returns_200(flask_test_client):

    response = flask_test_client.get('/health', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 200


def test_actions_endpoint_returns_200(flask_test_client):

    response = flask_test_client.get('/Relays/1/On', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302

    response = flask_test_client.get('/Relays/1/timer', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302

    response = flask_test_client.get('/Relays/1/Off', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302

    response = flask_test_client.get('/Relays/1/Off', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302

    response = flask_test_client.get('/Relays/2/auto', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302


def test_timer_endpoint_returns_200(flask_test_client):

    response = flask_test_client.get('/timer/Relays/3', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 200


def test_auto_endpoint_returns_200(flask_test_client):

    response = flask_test_client.get('/auto/Relays/2', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302


def test_set_timer_endpoint_returns_200(flask_test_client, method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')}):  # TODO test POST form

    response = flask_test_client.get('/set_timer', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302


def test_set_auto_endpoint_returns_200(flask_test_client):  # TODO test POST form

    response = flask_test_client.get('/set_auto', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302
