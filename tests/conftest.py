import pytest
from fastapi.testclient import TestClient
from backend.main import create_app

@pytest.fixture
def client(tmp_path):
    app=create_app(f'sqlite:///{tmp_path}/test.db',bootstrap_token='test-setup-token')
    with TestClient(app) as c:
        yield c

@pytest.fixture
def admin(client):
    response=client.post('/api/auth/bootstrap',json={
        'token':'test-setup-token','full_name':'Test Administrator',
        'email':'admin@test.example','password':'SafePassword123456','demo_data':False})
    assert response.status_code==201, response.text
    csrf=response.json()['csrfToken']
    return {'client':client,'csrf':csrf,'headers':{'X-CSRF-Token':csrf},'user':response.json()['user']}

@pytest.fixture
def records(admin):
    c=admin['client'];headers=admin['headers']
    sh=c.post('/api/showrooms',json={'name':'Downtown showroom','city':'New Delhi','address':'12 High Street'},headers=headers).json()
    customer=c.post('/api/customers',json={'full_name':'Nisha Patel','email':'nisha@client.example','phone':'9810012345','city':'Delhi'},headers=headers).json()
    vehicle={
        'vin':'A1234567890123456','make':'Hyundai','model':'Creta','variant':'SX(O)','year':2025,
        'price':1750000,'showroom_id':sh['id'],'mileage':5000,'status':'AVAILABLE'}
    v=c.post('/api/vehicles',json=vehicle,headers=headers)
    assert v.status_code==201,v.text
    return {'showroom':sh,'customer':customer,'vehicle':v.json(),'vehicleData':vehicle,**admin}

@pytest.fixture
def salesperson(records):
    c=records['client'];h=records['headers']
    u=c.post('/api/users',json={'full_name':'Sales Rep','email':'sales@test.example','role':'SALES','password':'SalesPassword1234'},headers=h)
    assert u.status_code==201,u.text
    s=TestClient(c.app)
    # separate authenticated cookie jar, same database
    auth=s.post('/api/auth/login',json={'email':'sales@test.example','password':'SalesPassword1234'})
    assert auth.status_code==200,auth.text
    yield {'client':s,'headers':{'X-CSRF-Token':auth.json()['csrfToken']},'user':u.json(),**{k:v for k,v in records.items() if k not in ('client','headers')}}
    s.close()
