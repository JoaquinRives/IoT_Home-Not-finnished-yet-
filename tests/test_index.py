

def test_index_health_200(flask_test_client):
    
    response = flask_test_client.get('/index')

    assert response.status_code == 200