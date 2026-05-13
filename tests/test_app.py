import pytest
from app import app, connect_to_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Force db connection to initialize mock db and seed data
        connect_to_db()
        yield client

def test_index_page(client):
    """Test that the index page loads."""
    rv = client.get('/')
    assert rv.status_code == 200

def test_get_countries(client):
    """Test retrieving countries API."""
    rv = client.get('/api/countries')
    assert rv.status_code == 200
    assert len(rv.json) > 0
    assert rv.json[0]['name'] == 'France'

def test_login_success(client):
    """Test successful login with admin user."""
    rv = client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
    assert rv.status_code == 200
    assert rv.json['success'] == True
    assert rv.json['user']['role'] == 'PeaceCouncilMember'

def test_login_failure(client):
    """Test failed login with incorrect password."""
    rv = client.post('/api/login', json={'username': 'admin', 'password': 'wrong'})
    assert rv.status_code == 401
    assert rv.json['success'] == False

def test_get_requests(client):
    """Test retrieving independence requests."""
    rv = client.get('/api/requests')
    assert rv.status_code == 200
    assert len(rv.json) > 0
