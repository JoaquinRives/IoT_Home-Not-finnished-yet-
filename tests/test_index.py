import base64

def test_index_health_200(flask_test_client):
    
    response = flask_test_client.get('/index', method='GET',
        headers={'Authorization': 'Basic ' + base64.b64encode(bytes('joaquin' + ":" + 'qwerty', 'ascii')).decode('ascii')})

    assert response.status_code == 200