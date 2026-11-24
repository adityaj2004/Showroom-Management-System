from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import pytest


def sale_payload(r,**change):
    return {'vehicle_id':r['vehicle']['id'],'customer_id':r['customer']['id'],
            'sale_price':1850000,'discount':50000,'payment_method':'UPI',**change}


def drive_payload(r,**change):
    return {'vehicle_id':r['vehicle']['id'],'customer_id':r['customer']['id'],
            'scheduled_at':(datetime.now()+timedelta(days=3)).isoformat(timespec='minutes'),**change}


def test_initial_setup_is_one_time_and_requires_token(client):
    assert client.get('/api/setup-status').json()['needsSetup'] is True
    bad=client.post('/api/auth/bootstrap',json={'token':'wrong','full_name':'Someone','email':'someone@test.example','password':'VeryLongPassword123'})
    assert bad.status_code==403
    response=client.post('/api/auth/bootstrap',json={'token':'test-setup-token','full_name':'First Admin','email':'first@test.example','password':'VeryLongPassword123'})
    assert response.status_code==201
    assert client.get('/api/setup-status').json()['needsSetup'] is False
    again=client.post('/api/auth/bootstrap',json={'token':'test-setup-token','full_name':'Second Admin','email':'second@test.example','password':'VeryLongPassword123'})
    assert again.status_code==403
    assert client.post('/api/auth/register',json={'full_name':'Uninvited','email':'no@test.example','password':'VeryLongPassword123'}).status_code==403


def test_unauthenticated_and_csrf_enforced(records):
    c=records['client'];id=records['vehicle']['id']
    assert c.get('/api/vehicles').status_code==200
    from fastapi.testclient import TestClient
    other=TestClient(c.app)
    assert other.get('/api/vehicles').status_code==401
    payload={**records['vehicleData'],'vin':'B1234567890123456'}
    assert c.post('/api/vehicles',json=payload).status_code==403
    assert c.post('/api/vehicles',json=payload,headers={'X-CSRF-Token':'fake'}).status_code==403
    assert c.get('/api/vehicles/'+str(id)).status_code==200
    # Secure content policies protect all pages.
    page=c.get('/')
    assert page.status_code==200
    assert "script-src 'self'" in page.headers['Content-Security-Policy']
    assert page.headers['X-Frame-Options']=='DENY'


def test_roles_are_enforced_by_backend(salesperson):
    c=salesperson['client'];h=salesperson['headers']
    r=salesperson
    assert c.get('/api/vehicles').status_code==200
    assert c.get('/api/users').status_code==403
    assert c.get('/api/audit').status_code==403
    assert c.post('/api/vehicles',json={**r['vehicleData'],'vin':'B1234567890123456'},headers=h).status_code==403
    assert c.post('/api/showrooms',json={'name':'Unauthorized','city':'Delhi','address':'Street'},headers=h).status_code==403
    assert c.delete(f'/api/customers/{r["customer"]["id"]}',headers=h).status_code==403
    assert c.post('/api/customers',json={'full_name':'Another Customer','phone':'9876543210'},headers=h).status_code==201


def test_sale_creation_reserves_vehicle_and_completion_sells(records):
    c=records['client'];h=records['headers'];v=records['vehicle']['id']
    response=c.post('/api/sales',json=sale_payload(records),headers=h)
    assert response.status_code==201,response.text
    sale=response.json()
    assert sale['status']=='PENDING'
    assert sale['finalAmount']==1800000
    assert sale['invoiceNumber'].startswith('NS-')
    assert c.get(f'/api/vehicles/{v}').json()['status']=='RESERVED'
    duplicate=c.post('/api/sales',json=sale_payload(records),headers=h)
    assert duplicate.status_code==409
    complete=c.patch(f'/api/sales/{sale["id"]}/status',json={'status':'COMPLETED'},headers=h)
    assert complete.status_code==200, complete.text
    assert c.get(f'/api/vehicles/{v}').json()['status']=='SOLD'
    assert c.patch(f'/api/sales/{sale["id"]}/status',json={'status':'CANCELLED'},headers=h).status_code==409
    assert c.delete(f'/api/sales/{sale["id"]}',headers=h).status_code==409
    dashboard=c.get('/api/dashboard').json()
    assert dashboard['completedSales']==1 and dashboard['revenue']==1800000


def test_cancel_sale_releases_stock(records):
    c=records['client'];h=records['headers'];v=records['vehicle']['id']
    sale=c.post('/api/sales',json=sale_payload(records),headers=h).json()
    resp=c.patch(f'/api/sales/{sale["id"]}/status',json={'status':'CANCELLED'},headers=h)
    assert resp.status_code==200
    assert c.get(f'/api/vehicles/{v}').json()['status']=='AVAILABLE'
    assert c.post('/api/sales',json=sale_payload(records),headers=h).status_code==201


def test_edit_pending_sale_switches_reserved_vehicle(records):
    c=records['client'];h=records['headers'];first=records['vehicle']['id']
    second=c.post('/api/vehicles',json={**records['vehicleData'],'vin':'B1234567890123456','model':'Verna'},headers=h).json()
    sale=c.post('/api/sales',json=sale_payload(records),headers=h).json()
    change=c.put(f'/api/sales/{sale["id"]}',json=sale_payload(records,vehicle_id=second['id']),headers=h)
    assert change.status_code==200, change.text
    assert c.get(f'/api/vehicles/{first}').json()['status']=='AVAILABLE'
    assert c.get(f'/api/vehicles/{second["id"]}').json()['status']=='RESERVED'


def test_sale_price_validation(records):
    c=records['client'];h=records['headers']
    res=c.post('/api/sales',json=sale_payload(records,sale_price=5000,discount=6000),headers=h)
    assert res.status_code==422
    assert c.get(f"/api/vehicles/{records['vehicle']['id']}").json()['status']=='AVAILABLE'


def test_booked_vehicle_cannot_be_manually_sold_or_deleted(records):
    c=records['client'];h=records['headers'];v=records['vehicle']['id']
    c.post('/api/sales',json=sale_payload(records),headers=h)
    assert c.patch(f'/api/vehicles/{v}/status',json={'status':'SOLD'},headers=h).status_code==400
    assert c.patch(f'/api/vehicles/{v}/status',json={'status':'IN_SERVICE'},headers=h).status_code==409
    assert c.delete(f'/api/vehicles/{v}',headers=h).status_code==409


def test_test_drive_conflicts_and_edit_validation(records):
    c=records['client'];h=records['headers']
    first=c.post('/api/test-drives',json=drive_payload(records),headers=h)
    assert first.status_code==201, first.text
    collision=c.post('/api/test-drives',json=drive_payload(records,scheduled_at=(datetime.now()+timedelta(days=3,minutes=30)).isoformat(timespec='minutes')),headers=h)
    assert collision.status_code==409
    second=c.post('/api/test-drives',json=drive_payload(records,scheduled_at=(datetime.now()+timedelta(days=4)).isoformat(timespec='minutes')),headers=h)
    assert second.status_code==201
    edit=c.put(f'/api/test-drives/{second.json()["id"]}',json=drive_payload(records),headers=h)
    assert edit.status_code==409
    closed=c.patch(f'/api/test-drives/{first.json()["id"]}/status',json={'status':'COMPLETED','feedback':'Excellent experience'},headers=h)
    assert closed.status_code==200
    assert closed.json()['feedback']=='Excellent experience'
    assert c.patch(f'/api/test-drives/{first.json()["id"]}/status',json={'status':'NO_SHOW'},headers=h).status_code==409


def test_cannot_book_test_drive_on_reserved_vehicle(records):
    c=records['client'];h=records['headers']
    c.post('/api/sales',json=sale_payload(records),headers=h)
    res=c.post('/api/test-drives',json=drive_payload(records),headers=h)
    assert res.status_code==409


def test_referential_integrity_and_unique_vin(records):
    c=records['client'];h=records['headers']
    assert c.post('/api/vehicles',json=records['vehicleData'],headers=h).status_code==409
    assert c.delete('/api/showrooms/'+str(records['showroom']['id']),headers=h).status_code==409
    d=c.post('/api/test-drives',json=drive_payload(records),headers=h)
    assert d.status_code==201
    assert c.delete('/api/customers/'+str(records['customer']['id']),headers=h).status_code==409


def test_staff_deactivation_and_active_admin_safety(records):
    c=records['client'];h=records['headers'];admin_id=records['user']['id']
    user=c.post('/api/users',json={'full_name':'Test Sales','email':'sales2@test.example','password':'LongPassword1234','role':'SALES'},headers=h)
    assert user.status_code==201,user.text
    uid=user.json()['id']
    deactivate=c.put(f'/api/users/{uid}',json={'full_name':'Test Sales','email':'sales2@test.example','role':'SALES','active':False},headers=h)
    assert deactivate.status_code==200
    login=c.post('/api/auth/login',json={'email':'sales2@test.example','password':'LongPassword1234'})
    assert login.status_code==401
    assert c.put(f'/api/users/{admin_id}',json={'full_name':'Test Administrator','email':'admin@test.example','role':'SALES'},headers=h).status_code==400
    assert c.delete(f'/api/users/{admin_id}',headers=h).status_code==400


def test_pagination_and_search(records):
    c=records['client'];h=records['headers']
    for i in range(14):
        c.post('/api/customers',json={'full_name':f'Customer Number {i}','phone':f'9876500{i:03}'},headers=h)
    page1=c.get('/api/customers?limit=5&page=1').json()
    page2=c.get('/api/customers?limit=5&page=2').json()
    assert len(page1['items'])==5 and page1['total']==15 and page1['pages']==3
    assert page1['items'][0]['id']!=page2['items'][0]['id']
    assert c.get('/api/customers?limit=10&q=Nisha').json()['total']==1
    assert c.get('/api/customers?limit=500').status_code==422


def test_sessions_logout_and_password_rotation(records):
    c=records['client'];h=records['headers']
    bad=c.put('/api/auth/change-password',json={'current_password':'wrong','new_password':'NewPassword123456'},headers=h)
    assert bad.status_code==400
    good=c.put('/api/auth/change-password',json={'current_password':'SafePassword123456','new_password':'NewPassword123456'},headers=h)
    assert good.status_code==200, good.text
    new_csrf=good.json()['csrfToken']
    assert c.get('/api/auth/me').status_code==200
    assert c.post('/api/auth/logout',headers={'X-CSRF-Token':new_csrf}).status_code==200
    assert c.get('/api/auth/me').status_code==401
    assert c.post('/api/auth/login',json={'email':'admin@test.example','password':'SafePassword123456'}).status_code==401
    assert c.post('/api/auth/login',json={'email':'admin@test.example','password':'NewPassword123456'}).status_code==200


def test_concurrent_sale_attempt_only_one_wins(records):
    c=records['client'];h=records['headers']
    def call(_): return c.post('/api/sales',json=sale_payload(records),headers=h).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=sorted(pool.map(call,range(2)))
    assert statuses==[201,409], statuses


def test_xss_content_is_data_not_html(records):
    c=records['client'];h=records['headers']
    xss='<img src=x onerror=alert(1)>'
    result=c.post('/api/customers',json={'full_name':xss,'phone':'9876543210'},headers=h)
    assert result.status_code==201
    assert xss in c.get('/api/customers').text # frontend escapes these strings when rendering.
