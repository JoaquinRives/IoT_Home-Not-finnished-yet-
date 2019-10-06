import base64
import RPi.GPIO as GPIO
from app.raspberry import Raspberry_1

rp1 = Raspberry_1()


def test_health_endpoint_returns_200(flask_test_client):

    response = flask_test_client.get('/health', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 200


def test_actions_endpoint(flask_test_client):

    response = flask_test_client.get('/Relays/1/On', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302

    # Test if the relay 1 has turned "ON"
    assert rp1.get_status(rp1.relay1)[0] == 'On'

    response = flask_test_client.get('/Relays/1/Off', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302

    # Test if the relay 1 has turned "OFF"
    assert rp1.get_status(rp1.relay1)[0] == 'Off'


def test_set_auto_endpoint(flask_test_client): 
    response = flask_test_client.get('/set_auto', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302


def test_set_timer_endpoint(flask_test_client):
    response = flask_test_client.get('/set_timer', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})

    response = flask_test_client.get('/set_timer', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 302


def test_timer_endpoint(flask_test_client):

    response = flask_test_client.get('/timer/Relays/3', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 200


def test_auto_endpoint(flask_test_client):

    response = flask_test_client.get('/auto/Relays/2', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})
    assert response.status_code == 200

