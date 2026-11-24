"""Northstar Showroom OS — independently implemented showroom operations API.
Run: python run.py. Database is SQLite by default; no external services required.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, date, timezone
from decimal import Decimal
import hashlib
import os
from pathlib import Path
import secrets
import time
from urllib.parse import urlparse

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Request, Response, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, or_, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, Session as DBSession
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .db import (Base, User, Session, InstallLock, Showroom, Vehicle, Customer, Sale, TestDrive,
                 AuditEvent, utcnow, make_engine, make_session_factory)
from .schemas import (LoginIn, BootstrapIn, RegisterIn, PasswordChange, UserIn,
                      ShowroomIn, VehicleIn, CustomerIn, SaleIn, TestDriveIn, StatusIn,
                      VehicleStatus, SaleStatus, DriveStatus, Role)

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')
PASSWORDS = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
LOGIN_ATTEMPTS: dict[str, list[float]] = defaultdict(list)


def error(status: int, message: str):
    raise HTTPException(status_code=status, detail=message)


def valid_password(value: str):
    if (len(value) < 12 or not any(c.isupper() for c in value)
            or not any(c.islower() for c in value) or not any(c.isdigit() for c in value)):
        error(422, 'Password must be at least 12 characters with uppercase, lowercase and a number')


def public_user(user: User):
    return {'id': user.id, 'fullName': user.full_name, 'email': user.email,
            'phone': user.phone, 'role': user.role, 'active': user.active,
            'createdAt': user.created_at.isoformat() if user.created_at else None}


def public_showroom(s: Showroom):
    return {'id': s.id, 'name': s.name, 'city': s.city, 'address': s.address,
            'phone': s.phone, 'createdAt': s.created_at.isoformat()}


def public_vehicle(v: Vehicle):
    return {'id': v.id, 'vin': v.vin, 'make': v.make, 'model': v.model, 'variant': v.variant,
            'year': v.year, 'color': v.color, 'fuelType': v.fuel_type,
            'transmission': v.transmission, 'price': float(v.price), 'mileage': v.mileage,
            'status': v.status, 'showroomId': v.showroom_id,
            'showroomName': v.showroom.name if v.showroom else '',
            'description': v.description, 'createdAt': v.created_at.isoformat()}


def public_customer(c: Customer):
    return {'id': c.id, 'fullName': c.full_name, 'email': c.email, 'phone': c.phone,
            'city': c.city, 'address': c.address, 'notes': c.notes,
            'createdAt': c.created_at.isoformat()}


def public_sale(s: Sale):
    return {'id': s.id, 'invoiceNumber': s.invoice_number, 'vehicleId': s.vehicle_id,
            'vehicleLabel': f'{s.vehicle.year} {s.vehicle.make} {s.vehicle.model}',
            'customerId': s.customer_id, 'customerName': s.customer.full_name,
            'salespersonId': s.salesperson_id, 'salespersonName': s.salesperson.full_name,
            'salePrice': float(s.sale_price), 'discount': float(s.discount),
            'finalAmount': float(s.final_amount), 'paymentMethod': s.payment_method,
            'saleDate': s.sale_date, 'status': s.status, 'notes': s.notes,
            'createdAt': s.created_at.isoformat()}


def public_drive(d: TestDrive):
    return {'id': d.id, 'vehicleId': d.vehicle_id,
            'vehicleLabel': f'{d.vehicle.year} {d.vehicle.make} {d.vehicle.model}',
            'customerId': d.customer_id, 'customerName': d.customer.full_name,
            'salespersonId': d.salesperson_id, 'salespersonName': d.salesperson.full_name,
            'scheduledAt': d.scheduled_at.replace(tzinfo=timezone.utc).isoformat(timespec='minutes'), 'status': d.status,
            'feedback': d.feedback, 'createdAt': d.created_at.isoformat()}


def paginate(db, stmt, model, page: int, limit: int):
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    results = db.scalars(stmt.limit(limit).offset((page - 1) * limit)).unique().all()
    return {'items': [model(x) for x in results], 'total': total,
            'page': page, 'limit': limit, 'pages': max(1, (total + limit - 1) // limit)}


def record(db, user_id, action, target):
    db.add(AuditEvent(user_id=user_id, action=action, target=target))


def get_required(db, cls, record_id):
    item = db.get(cls, record_id)
    if item is None:
        error(404, f'{cls.__name__} not found')
    return item


def ensure_sale_references(db, vehicle_id, customer_id, salesperson_id):
    v = get_required(db, Vehicle, vehicle_id)
    get_required(db, Customer, customer_id)
    seller = get_required(db, User, salesperson_id)
    if not seller.active:
        error(400, 'Salesperson account is inactive')
    return v


def seed_demo(db, admin_id: int):
    """Optional demo fixtures, invoked only by the verified first-admin setup."""
    showroom_data = [
        ('Northstar Delhi Central', 'New Delhi', 'Connaught Place, New Delhi', '+91 11 4000 2010'),
        ('Northstar Gurugram', 'Gurugram', 'Golf Course Road, Gurugram', '+91 124 400 2011'),
        ('Northstar Noida', 'Noida', 'Sector 18, Noida', '+91 120 400 2012')]
    showrooms = [Showroom(name=n, city=c, address=a, phone=p) for n, c, a, p in showroom_data]
    db.add_all(showrooms)
    db.flush()
    cars = [
        ('NSR241000001', 'Hyundai', 'Creta', 'SX(O)', 2025, 'Titan Grey', 'Diesel', 'Automatic', 1899000, 12500, 0),
        ('NSR241000002', 'Tata', 'Nexon', 'Fearless+', 2025, 'Pristine White', 'Petrol', 'Manual', 1465000, 6200, 0),
        ('NSR241000003', 'Mahindra', 'XUV700', 'AX7 Luxury', 2024, 'Midnight Black', 'Diesel', 'Automatic', 2490000, 18400, 1),
        ('NSR241000004', 'Kia', 'Seltos', 'GT Line', 2025, 'Pewter Olive', 'Petrol', 'Automatic', 1950000, 4100, 0),
        ('NSR241000005', 'Maruti Suzuki', 'Grand Vitara', 'Alpha+', 2024, 'Arctic White', 'Hybrid', 'Automatic', 1760000, 11200, 2),
        ('NSR241000006', 'Honda', 'Elevate', 'ZX CVT', 2025, 'Phoenix Orange', 'Petrol', 'Automatic', 1640000, 2300, 1),
        ('NSR241000007', 'Toyota', 'Innova Hycross', 'VX', 2024, 'Silver', 'Hybrid', 'Automatic', 2850000, 21500, 2),
        ('NSR241000008', 'Volkswagen', 'Virtus', 'GT Plus', 2025, 'Lava Blue', 'Petrol', 'Automatic', 1835000, 7600, 0),
        ('NSR241000009', 'Skoda', 'Kushaq', 'Monte Carlo', 2025, 'Carbon Steel', 'Petrol', 'Automatic', 1725000, 3500, 1),
        ('NSR241000010', 'MG', 'Hector', 'Sharp Pro', 2024, 'Glaze Red', 'Diesel', 'Manual', 2040000, 18200, 2),
        ('NSR241000011', 'Hyundai', 'Verna', 'SX Turbo', 2025, 'Fiery Red', 'Petrol', 'Automatic', 1610000, 2900, 0),
        ('NSR241000012', 'Tata', 'Harrier', 'Adventure+', 2024, 'Oberon Black', 'Diesel', 'Manual', 2240000, 17200, 1),
    ]
    vehicles = [Vehicle(vin=v, make=m, model=mo, variant=va, year=y, color=c,
                        fuel_type=f, transmission=t, price=p, mileage=km,
                        showroom_id=showrooms[sh].id) for v, m, mo, va, y, c, f, t, p, km, sh in cars]
    db.add_all(vehicles)
    customers = [
        Customer(full_name='Aarav Mehta', email='aarav@example.com', phone='9810012345', city='New Delhi'),
        Customer(full_name='Priya Sharma', email='priya@example.com', phone='9810012346', city='Gurugram'),
        Customer(full_name='Rohan Kapoor', email='rohan@example.com', phone='9810012347', city='Noida'),
        Customer(full_name='Ananya Singh', email='ananya@example.com', phone='9810012348', city='New Delhi'),
        Customer(full_name='Ishaan Gupta', email='ishaan@example.com', phone='9810012349', city='Gurugram'),
        Customer(full_name='Simran Kaur', email='simran@example.com', phone='9810012350', city='Noida'),
    ]
    db.add_all(customers)
    db.flush()
    today = date.today()
    for idx, vehicle_idx in enumerate([0, 2, 4, 7, 10]):
        v = vehicles[vehicle_idx]
        done = idx < 3
        v.status = 'SOLD' if done else 'RESERVED'
        price = Decimal(str(v.price))
        discount = Decimal(25000 + idx * 5000)
        sale = Sale(invoice_number=f'NS-{today.year}-D{idx + 1:04d}', vehicle_id=v.id,
                    customer_id=customers[idx].id, salesperson_id=admin_id,
                    sale_price=price, discount=discount, final_amount=price - discount,
                    payment_method=['UPI', 'FINANCE', 'BANK_TRANSFER', 'CARD', 'UPI'][idx],
                    sale_date=str(today - timedelta(days=idx * 5)),
                    status='COMPLETED' if done else 'PENDING')
        db.add(sale)
    db.flush()
    for idx, vehicle_idx in enumerate([1, 3, 5, 8]):
        d = TestDrive(vehicle_id=vehicles[vehicle_idx].id,
                      customer_id=customers[idx + 1].id, salesperson_id=admin_id,
                      scheduled_at=utcnow() + timedelta(days=idx + 1, hours=3), status='SCHEDULED')
        db.add(d)
    vehicles[11].status = 'IN_SERVICE'


def create_app(database_url: str | None = None, bootstrap_token: str | None = None,
               allow_public_registration: bool | None = None) -> FastAPI:
    default_url = f'sqlite:///{ROOT / "data" / "showroom.db"}'
    url = database_url or os.getenv('DATABASE_URL', default_url)
    if url.startswith('sqlite:///') and url != 'sqlite:///:memory:':
        Path(url.removeprefix('sqlite:///')).parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(url)
    Base.metadata.create_all(engine)
    SessionLocal = make_session_factory(engine)
    setup_token = bootstrap_token or os.getenv('BOOTSTRAP_TOKEN') or secrets.token_urlsafe(24)
    registration = allow_public_registration if allow_public_registration is not None else os.getenv('ALLOW_PUBLIC_REGISTRATION', '').lower() == 'true'
    cookie_secure = os.getenv('COOKIE_SECURE', '').lower() == 'true'

    @asynccontextmanager
    async def lifespan(_app):
        with SessionLocal() as db:
            if not db.scalar(select(func.count(User.id))):
                print('\n' + '=' * 65, flush=True)
                print('NORTHSTAR FIRST-ADMIN SETUP TOKEN:', setup_token, flush=True)
                print('Enter this token on the setup screen. It is one-time only.', flush=True)
                print('=' * 65 + '\n', flush=True)
        yield

    app = FastAPI(title='Northstar Showroom OS', version='1.0.0', docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.setup_token = setup_token
    app.state.SessionLocal = SessionLocal
    app.state.engine = engine
    hosts = [host.strip() for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',') if host.strip()]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

    @app.middleware('http')
    async def protect(request: Request, call_next):
        origin = request.headers.get('origin')
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and origin:
            supplied = urlparse(origin)
            if supplied.netloc != request.url.netloc or supplied.scheme not in ('http', 'https'):
                return JSONResponse({'message': 'Cross-origin requests are not allowed'}, status_code=403)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        if cookie_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        if request.url.path.startswith('/api'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(HTTPException)
    async def http_error(_request, exc: HTTPException):
        return JSONResponse({'message': exc.detail}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, exc):
        details = [{'field': '.'.join(str(x) for x in e['loc'] if x != 'body'), 'message': e['msg']}
                   for e in exc.errors()]
        return JSONResponse({'message': 'Check the highlighted fields', 'errors': details}, status_code=422)

    def get_db():
        with SessionLocal() as db:
            yield db

    def current_user(request: Request, db: DBSession = Depends(get_db)):
        token = request.cookies.get('ns_session')
        if not token:
            error(401, 'Sign in to continue')
        digest = hashlib.sha256(token.encode()).hexdigest()
        session = db.scalar(select(Session).where(Session.token_hash == digest))
        if not session or session.expires_at <= utcnow() or not session.user.active:
            error(401, 'Session expired. Please sign in again')
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            csrf = request.headers.get('X-CSRF-Token', '')
            if not secrets.compare_digest(csrf, session.csrf_token):
                error(403, 'Security token missing or expired. Refresh and try again')
        request.state.session = session
        return session.user

    def permission(*roles):
        def check(user: User = Depends(current_user)):
            if user.role not in roles:
                error(403, 'You do not have permission for this action')
            return user
        return check

    def audit_commit(db, user_id, action, target):
        record(db, user_id, action, target)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            error(409, 'This change conflicts with an existing record')

    def set_session(response: Response, db, user: User):
        token = secrets.token_urlsafe(48)
        csrf = secrets.token_urlsafe(32)
        expires = utcnow() + timedelta(hours=12)
        db.add(Session(token_hash=hashlib.sha256(token.encode()).hexdigest(),
                       csrf_token=csrf, user_id=user.id, expires_at=expires))
        db.commit()
        response.set_cookie('ns_session', token, max_age=43200,
                            httponly=True, secure=cookie_secure, samesite='strict', path='/')
        return {'user': public_user(user), 'csrfToken': csrf}

    @app.get('/api/health')
    def health():
        return {'status': 'ok'}

    @app.get('/api/setup-status')
    def setup_status(db=Depends(get_db)):
        return {'needsSetup': db.scalar(select(func.count(User.id))) == 0,
                'registrationEnabled': registration}

    @app.post('/api/auth/bootstrap', status_code=201)
    def bootstrap(data: BootstrapIn, response: Response, db=Depends(get_db)):
        if db.scalar(select(func.count(User.id))) > 0:
            error(403, 'Setup has already been completed')
        if not secrets.compare_digest(data.token, setup_token):
            error(403, 'Invalid setup token')
        valid_password(data.password)
        user = User(full_name=data.full_name, email=data.email,
                    password_hash=PASSWORDS.hash(data.password), role='ADMIN')
        db.add(InstallLock(id=1))
        db.add(user)
        try:
            db.flush()
            if data.demo_data:
                seed_demo(db, user.id)
            db.commit()
        except IntegrityError:
            db.rollback()
            error(409, 'An administrator already exists')
        return set_session(response, db, user)

    @app.post('/api/auth/register', status_code=201)
    def register(data: RegisterIn, response: Response, db=Depends(get_db)):
        if not registration or not db.scalar(select(func.count(User.id))):
            error(403, 'Public registration is disabled. Contact your administrator')
        valid_password(data.password)
        user = User(full_name=data.full_name, email=data.email,
                    phone=data.phone, password_hash=PASSWORDS.hash(data.password), role='SALES')
        db.add(user)
        try: db.commit()
        except IntegrityError:
            db.rollback()
            error(409, 'Email already registered')
        return set_session(response, db, user)

    @app.post('/api/auth/login')
    def login(data: LoginIn, response: Response, request: Request, db=Depends(get_db)):
        key = f'{request.client.host if request.client else "unknown"}:{data.email}'
        now = time.monotonic()
        LOGIN_ATTEMPTS[key] = [t for t in LOGIN_ATTEMPTS[key] if now - t < 900]
        if len(LOGIN_ATTEMPTS[key]) >= 5:
            error(429, 'Too many sign-in attempts. Try again after 15 minutes')
        user = db.scalar(select(User).where(User.email == data.email))
        try:
            ok = bool(user and PASSWORDS.verify(user.password_hash, data.password))
        except (VerifyMismatchError, VerificationError):
            ok = False
        if not ok or not user.active:
            LOGIN_ATTEMPTS[key].append(now)
            error(401, 'Invalid email or password')
        LOGIN_ATTEMPTS.pop(key, None)
        return set_session(response, db, user)

    @app.get('/api/auth/me')
    def me(request: Request, user: User = Depends(current_user)):
        return {'user': public_user(user), 'csrfToken': request.state.session.csrf_token}

    @app.post('/api/auth/logout')
    def logout(request: Request, response: Response, db=Depends(get_db), user=Depends(current_user)):
        db.delete(request.state.session)
        db.commit()
        response.delete_cookie('ns_session', path='/')
        return {'ok': True}

    @app.put('/api/auth/change-password')
    def change_password(data: PasswordChange, request: Request, response: Response,
                        db=Depends(get_db), user: User = Depends(current_user)):
        try: valid = PASSWORDS.verify(user.password_hash, data.current_password)
        except (VerifyMismatchError, VerificationError): valid = False
        if not valid:
            error(400, 'Current password is incorrect')
        valid_password(data.new_password)
        user.password_hash = PASSWORDS.hash(data.new_password)
        # Revoke every session; issue a fresh one after saving password.
        db.execute(delete(Session).where(Session.user_id == user.id))
        db.commit()
        return set_session(response, db, user)

    @app.get('/api/users/{item_id}')
    def get_user(item_id: int, db=Depends(get_db), user=Depends(permission('ADMIN','MANAGER'))):
        return public_user(get_required(db, User, item_id))

    @app.get('/api/users')
    def list_users(q: str = '', page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                   db=Depends(get_db), user=Depends(permission('ADMIN','MANAGER'))):
        stmt = select(User)
        if q: stmt = stmt.where(or_(User.full_name.ilike(f'%{q[:100]}%'), User.email.ilike(f'%{q[:100]}%')))
        return paginate(db, stmt.order_by(User.id.desc()), public_user, page, limit)

    @app.post('/api/users', status_code=201)
    def create_user(data: UserIn, db=Depends(get_db), user=Depends(permission('ADMIN'))):
        if not data.password: error(422, 'Password is required for a new staff member')
        valid_password(data.password)
        u = User(full_name=data.full_name, email=data.email, phone=data.phone,
                 password_hash=PASSWORDS.hash(data.password), role=data.role.value, active=data.active)
        db.add(u)
        audit_commit(db, user.id, 'STAFF_CREATED', data.email)
        return public_user(u)

    @app.put('/api/users/{item_id}')
    def edit_user(item_id: int, data: UserIn, db=Depends(get_db), user=Depends(permission('ADMIN'))):
        u = get_required(db, User, item_id)
        if u.id == user.id and (not data.active or data.role != Role.ADMIN):
            error(400, 'You cannot deactivate or demote your own account')
        if u.role == 'ADMIN' and (not data.active or data.role != Role.ADMIN):
            others = db.scalar(select(func.count(User.id)).where(User.role=='ADMIN', User.active==True, User.id!=u.id))
            if not others: error(400, 'The last active administrator cannot be removed')
        u.full_name, u.email, u.phone, u.role, u.active = data.full_name, data.email, data.phone, data.role.value, data.active
        if data.password:
            valid_password(data.password)
            u.password_hash = PASSWORDS.hash(data.password)
            db.execute(delete(Session).where(Session.user_id == u.id))
        audit_commit(db, user.id, 'STAFF_UPDATED', str(item_id))
        return public_user(u)

    @app.delete('/api/users/{item_id}')
    def delete_user(item_id: int, db=Depends(get_db), user=Depends(permission('ADMIN'))):
        u = get_required(db, User, item_id)
        if u.id == user.id: error(400, 'You cannot delete your own account')
        if db.scalar(select(func.count()).select_from(Sale).where(Sale.salesperson_id==item_id)) or db.scalar(select(func.count()).select_from(TestDrive).where(TestDrive.salesperson_id==item_id)):
            error(409, 'This staff member has activity history. Deactivate instead')
        db.delete(u)
        audit_commit(db, user.id, 'STAFF_DELETED', str(item_id))
        return {'ok': True}

    @app.get('/api/showrooms/{item_id}')
    def get_showroom(item_id: int, db=Depends(get_db), user=Depends(current_user)):
        return public_showroom(get_required(db, Showroom, item_id))

    @app.get('/api/showrooms')
    def list_showrooms(q: str = '', page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100),
                       db=Depends(get_db), user=Depends(current_user)):
        stmt = select(Showroom)
        if q: stmt = stmt.where(or_(Showroom.name.ilike(f'%{q[:100]}%'), Showroom.city.ilike(f'%{q[:100]}%')))
        return paginate(db, stmt.order_by(Showroom.id.desc()), public_showroom, page, limit)

    @app.post('/api/showrooms', status_code=201)
    def create_showroom(data: ShowroomIn, db=Depends(get_db), user=Depends(permission('ADMIN'))):
        sh = Showroom(**data.model_dump())
        db.add(sh)
        audit_commit(db, user.id, 'SHOWROOM_CREATED', data.name)
        return public_showroom(sh)

    @app.put('/api/showrooms/{item_id}')
    def edit_showroom(item_id: int, data: ShowroomIn, db=Depends(get_db), user=Depends(permission('ADMIN'))):
        sh = get_required(db, Showroom, item_id)
        for k,v in data.model_dump().items(): setattr(sh,k,v)
        audit_commit(db, user.id, 'SHOWROOM_UPDATED', str(item_id))
        return public_showroom(sh)

    @app.delete('/api/showrooms/{item_id}')
    def delete_showroom(item_id: int, db=Depends(get_db), user=Depends(permission('ADMIN'))):
        sh = get_required(db, Showroom, item_id)
        if db.scalar(select(func.count(Vehicle.id)).where(Vehicle.showroom_id==item_id)):
            error(409, 'Move the vehicles to another showroom before deleting this location')
        db.delete(sh)
        audit_commit(db, user.id, 'SHOWROOM_DELETED', str(item_id))
        return {'ok': True}

    @app.get('/api/vehicles/{item_id}')
    def get_vehicle(item_id: int, db=Depends(get_db), user=Depends(current_user)):
        return public_vehicle(get_required(db, Vehicle, item_id))

    @app.get('/api/vehicles')
    def list_vehicles(q: str = '', status: str = '', showroom_id: int | None = None, showroomId: int | None = None,
                      page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                      db=Depends(get_db), user=Depends(current_user)):
        stmt = select(Vehicle).options(joinedload(Vehicle.showroom))
        if q: stmt = stmt.where(or_(Vehicle.make.ilike(f'%{q[:100]}%'),Vehicle.model.ilike(f'%{q[:100]}%'),Vehicle.vin.ilike(f'%{q[:100]}%')))
        if status: stmt = stmt.where(Vehicle.status==status)
        chosen_showroom = showroom_id or showroomId
        if chosen_showroom: stmt = stmt.where(Vehicle.showroom_id==chosen_showroom)
        return paginate(db, stmt.order_by(Vehicle.id.desc()), public_vehicle, page, limit)

    @app.post('/api/vehicles', status_code=201)
    def create_vehicle(data: VehicleIn, db=Depends(get_db), user=Depends(permission('ADMIN','MANAGER'))):
        get_required(db, Showroom, data.showroom_id)
        if data.status not in (VehicleStatus.AVAILABLE, VehicleStatus.IN_SERVICE):
            error(400, 'Reserved and sold statuses can only come from sales')
        vals = data.model_dump()
        vals['status'] = data.status.value
        v = Vehicle(**vals)
        db.add(v)
        audit_commit(db, user.id, 'VEHICLE_CREATED', data.vin)
        db.refresh(v)
        return public_vehicle(v)

    @app.put('/api/vehicles/{item_id}')
    def edit_vehicle(item_id: int, data: VehicleIn, db=Depends(get_db), user=Depends(permission('ADMIN','MANAGER'))):
        v = get_required(db, Vehicle, item_id)
        get_required(db, Showroom, data.showroom_id)
        if data.status.value != v.status and (v.status in ('RESERVED','SOLD') or data.status not in (VehicleStatus.AVAILABLE, VehicleStatus.IN_SERVICE)):
            error(409, 'Sale-controlled vehicle status cannot be changed manually')
        vals = data.model_dump()
        vals['status'] = data.status.value
        for k,value in vals.items(): setattr(v,k,value)
        audit_commit(db, user.id, 'VEHICLE_UPDATED', str(item_id))
        db.refresh(v)
        return public_vehicle(v)

    @app.patch('/api/vehicles/{item_id}/status')
    def vehicle_status(item_id: int, data: StatusIn, db=Depends(get_db), user=Depends(permission('ADMIN','MANAGER'))):
        if data.status not in ('AVAILABLE','IN_SERVICE'):
            error(400, 'Only Available or In Service may be set manually')
        v = get_required(db, Vehicle, item_id)
        if v.status in ('RESERVED','SOLD'):
            error(409, 'This vehicle status is controlled by its sale')
        v.status = data.status
        audit_commit(db, user.id, 'VEHICLE_STATUS_CHANGED', f'{item_id}:{data.status}')
        db.refresh(v)
        return public_vehicle(v)

    @app.delete('/api/vehicles/{item_id}')
    def delete_vehicle(item_id: int, db=Depends(get_db), user=Depends(permission('ADMIN','MANAGER'))):
        v = get_required(db, Vehicle, item_id)
        if db.scalar(select(func.count(Sale.id)).where(Sale.vehicle_id==item_id)) or db.scalar(select(func.count(TestDrive.id)).where(TestDrive.vehicle_id==item_id)):
            error(409, 'Vehicle has sales or test-drive history. It cannot be deleted')
        db.delete(v)
        audit_commit(db, user.id, 'VEHICLE_DELETED', str(item_id))
        return {'ok': True}

    @app.get('/api/customers/{item_id}')
    def get_customer(item_id: int, db=Depends(get_db), user=Depends(current_user)):
        return public_customer(get_required(db, Customer, item_id))

    @app.get('/api/customers')
    def list_customers(q: str = '', page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                       db=Depends(get_db), user=Depends(current_user)):
        stmt = select(Customer)
        if q: stmt = stmt.where(or_(Customer.full_name.ilike(f'%{q[:100]}%'),Customer.phone.ilike(f'%{q[:100]}%'),Customer.email.ilike(f'%{q[:100]}%')))
        return paginate(db, stmt.order_by(Customer.id.desc()), public_customer, page, limit)

    @app.post('/api/customers', status_code=201)
    def create_customer(data: CustomerIn, db=Depends(get_db), user=Depends(current_user)):
        c = Customer(**data.model_dump())
        db.add(c)
        audit_commit(db, user.id, 'CUSTOMER_CREATED', data.full_name)
        return public_customer(c)

    @app.put('/api/customers/{item_id}')
    def edit_customer(item_id: int, data: CustomerIn, db=Depends(get_db), user=Depends(current_user)):
        c = get_required(db, Customer, item_id)
        for k,v in data.model_dump().items(): setattr(c,k,v)
        audit_commit(db, user.id, 'CUSTOMER_UPDATED', str(item_id))
        return public_customer(c)

    @app.delete('/api/customers/{item_id}')
    def delete_customer(item_id: int, db=Depends(get_db), user=Depends(permission('ADMIN','MANAGER'))):
        c = get_required(db, Customer, item_id)
        if db.scalar(select(func.count(Sale.id)).where(Sale.customer_id==item_id)) or db.scalar(select(func.count(TestDrive.id)).where(TestDrive.customer_id==item_id)):
            error(409, 'Customer has activity history and cannot be deleted')
        db.delete(c)
        audit_commit(db, user.id, 'CUSTOMER_DELETED', str(item_id))
        return {'ok': True}

    @app.get('/api/sales/{item_id}')
    def get_sale(item_id: int, db=Depends(get_db), user=Depends(current_user)):
        return public_sale(get_required(db, Sale, item_id))

    @app.get('/api/sales')
    def list_sales(q: str = '', status: str = '', page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                   db=Depends(get_db), user=Depends(current_user)):
        stmt = select(Sale).options(joinedload(Sale.vehicle), joinedload(Sale.customer), joinedload(Sale.salesperson))
        if q:
            stmt = stmt.join(Sale.customer).join(Sale.vehicle).where(or_(Sale.invoice_number.ilike(f'%{q[:100]}%'), Customer.full_name.ilike(f'%{q[:100]}%'),Vehicle.model.ilike(f'%{q[:100]}%')))
        if status: stmt = stmt.where(Sale.status==status)
        return paginate(db, stmt.order_by(Sale.id.desc()), public_sale, page, limit)

    @app.post('/api/sales', status_code=201)
    def create_sale(data: SaleIn, db=Depends(get_db), user=Depends(current_user)):
        seller = data.salesperson_id or user.id
        ensure_sale_references(db, data.vehicle_id, data.customer_id, seller)
        # Conditional UPDATE is the concurrency gate: two requests cannot reserve the same vehicle.
        claim = db.execute(update(Vehicle).where(Vehicle.id==data.vehicle_id,
                       Vehicle.status=='AVAILABLE').values(status='RESERVED'))
        if claim.rowcount != 1:
            db.rollback()
            error(409, 'This vehicle is no longer available')
        s = Sale(invoice_number=f'TMP-{secrets.token_hex(8)}', vehicle_id=data.vehicle_id,
                 customer_id=data.customer_id, salesperson_id=seller,
                 sale_price=data.sale_price, discount=data.discount,
                 final_amount=data.sale_price - data.discount,
                 payment_method=data.payment_method.value, sale_date=data.sale_date.isoformat(),
                 notes=data.notes, status='PENDING')
        db.add(s)
        db.flush()
        s.invoice_number = f'NS-{date.today().year}-{s.id:05d}'
        audit_commit(db, user.id, 'SALE_CREATED', s.invoice_number)
        db.refresh(s)
        return public_sale(s)

    @app.put('/api/sales/{item_id}')
    def edit_sale(item_id: int, data: SaleIn, db=Depends(get_db), user=Depends(current_user)):
        s = get_required(db, Sale, item_id)
        if s.status != 'PENDING': error(409, 'Only pending sales can be edited')
        seller = data.salesperson_id or user.id
        ensure_sale_references(db, data.vehicle_id, data.customer_id, seller)
        if s.vehicle_id != data.vehicle_id:
            claim = db.execute(update(Vehicle).where(Vehicle.id==data.vehicle_id,Vehicle.status=='AVAILABLE').values(status='RESERVED'))
            if claim.rowcount != 1:
                db.rollback(); error(409, 'New vehicle is no longer available')
            db.execute(update(Vehicle).where(Vehicle.id==s.vehicle_id,Vehicle.status=='RESERVED').values(status='AVAILABLE'))
        s.vehicle_id, s.customer_id, s.salesperson_id = data.vehicle_id, data.customer_id, seller
        s.sale_price, s.discount = data.sale_price, data.discount
        s.final_amount = data.sale_price - data.discount
        s.payment_method, s.sale_date, s.notes = data.payment_method.value, data.sale_date.isoformat(), data.notes
        audit_commit(db, user.id, 'SALE_UPDATED', s.invoice_number)
        db.refresh(s)
        return public_sale(s)

    @app.patch('/api/sales/{item_id}/status')
    def sale_status(item_id: int, data: StatusIn, db=Depends(get_db), user=Depends(permission('ADMIN','MANAGER'))):
        if data.status not in ('COMPLETED','CANCELLED'):
            error(400, 'A sale may only be completed or cancelled')
        updated = db.execute(update(Sale).where(Sale.id==item_id,Sale.status=='PENDING').values(status=data.status))
        if updated.rowcount != 1:
            db.rollback()
            get_required(db, Sale, item_id)
            error(409, 'Sale is not pending or has already been processed')
        s = get_required(db, Sale, item_id)
        new_status = 'SOLD' if data.status == 'COMPLETED' else 'AVAILABLE'
        vehicle_update = db.execute(update(Vehicle).where(Vehicle.id==s.vehicle_id,Vehicle.status=='RESERVED').values(status=new_status))
        if vehicle_update.rowcount != 1:
            db.rollback(); error(409, 'Vehicle reservation is inconsistent. No changes were saved')
        audit_commit(db, user.id, 'SALE_STATUS_CHANGED', f'{s.invoice_number}:{data.status}')
        db.refresh(s)
        return public_sale(s)

    @app.delete('/api/sales/{item_id}')
    def delete_sale(item_id: int, db=Depends(get_db), user=Depends(permission('ADMIN'))):
        s = get_required(db, Sale, item_id)
        if s.status == 'COMPLETED': error(409, 'Completed sales are financial history and cannot be deleted')
        if s.status == 'PENDING':
            db.execute(update(Vehicle).where(Vehicle.id==s.vehicle_id,Vehicle.status=='RESERVED').values(status='AVAILABLE'))
        db.delete(s)
        audit_commit(db, user.id, 'SALE_DELETED', str(item_id))
        return {'ok': True}

    @app.get('/api/test-drives/{item_id}')
    def get_drive(item_id: int, db=Depends(get_db), user=Depends(current_user)):
        return public_drive(get_required(db, TestDrive, item_id))

    @app.get('/api/test-drives')
    def list_drives(q: str = '', status: str = '', page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                    db=Depends(get_db), user=Depends(current_user)):
        stmt = select(TestDrive).options(joinedload(TestDrive.vehicle), joinedload(TestDrive.customer), joinedload(TestDrive.salesperson))
        if q:
            stmt = stmt.join(TestDrive.customer).join(TestDrive.vehicle).where(or_(Customer.full_name.ilike(f'%{q[:100]}%'), Vehicle.model.ilike(f'%{q[:100]}%')))
        if status: stmt = stmt.where(TestDrive.status==status)
        return paginate(db, stmt.order_by(TestDrive.scheduled_at.desc()), public_drive, page, limit)

    def normalize_utc(value: datetime):
        return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value

    def validate_slot(db, vehicle_id: int, when: datetime, exclude: int | None = None):
        # A harmless conditional UPDATE acquires a SQLite write lock before the availability
        # and booking reads. Concurrent schedulers therefore cannot both accept the same slot.
        db.execute(update(Vehicle).where(Vehicle.id == vehicle_id).values(mileage=Vehicle.mileage))
        v = get_required(db, Vehicle, vehicle_id)
        if v.status != 'AVAILABLE': error(409, 'Select an available vehicle for the test drive')
        when = normalize_utc(when)
        if when < utcnow() - timedelta(minutes=1):
            error(400, 'Choose a future appointment time')
        stmt = select(TestDrive).where(TestDrive.vehicle_id==vehicle_id,
                     TestDrive.status=='SCHEDULED', TestDrive.scheduled_at > when-timedelta(hours=1),
                     TestDrive.scheduled_at < when+timedelta(hours=1))
        if exclude: stmt = stmt.where(TestDrive.id != exclude)
        if db.scalar(stmt): error(409, 'This vehicle already has a test drive within one hour of that time')

    @app.post('/api/test-drives', status_code=201)
    def create_drive(data: TestDriveIn, db=Depends(get_db), user=Depends(current_user)):
        seller = data.salesperson_id or user.id
        get_required(db, Customer, data.customer_id)
        if not get_required(db, User, seller).active: error(400, 'Salesperson is inactive')
        validate_slot(db, data.vehicle_id, data.scheduled_at)
        d = TestDrive(vehicle_id=data.vehicle_id, customer_id=data.customer_id,
                      salesperson_id=seller, scheduled_at=normalize_utc(data.scheduled_at),
                      status='SCHEDULED', feedback=data.feedback)
        db.add(d)
        db.flush()
        audit_commit(db, user.id, 'TEST_DRIVE_CREATED', str(d.id))
        db.refresh(d)
        return public_drive(d)

    @app.put('/api/test-drives/{item_id}')
    def edit_drive(item_id: int, data: TestDriveIn, db=Depends(get_db), user=Depends(current_user)):
        d = get_required(db, TestDrive, item_id)
        if d.status != 'SCHEDULED': error(409, 'Only scheduled test drives can be edited')
        seller = data.salesperson_id or user.id
        get_required(db, Customer, data.customer_id)
        if not get_required(db, User, seller).active: error(400, 'Salesperson is inactive')
        validate_slot(db, data.vehicle_id, data.scheduled_at, exclude=item_id)
        d.vehicle_id, d.customer_id, d.salesperson_id = data.vehicle_id, data.customer_id, seller
        d.scheduled_at, d.feedback = normalize_utc(data.scheduled_at), data.feedback
        audit_commit(db, user.id, 'TEST_DRIVE_UPDATED', str(item_id))
        db.refresh(d)
        return public_drive(d)

    @app.patch('/api/test-drives/{item_id}/status')
    def drive_status(item_id: int, data: StatusIn, db=Depends(get_db), user=Depends(current_user)):
        if data.status not in ('COMPLETED','NO_SHOW','CANCELLED'):
            error(400, 'Invalid test-drive status transition')
        d = get_required(db, TestDrive, item_id)
        if d.status != 'SCHEDULED': error(409, 'This test drive is already closed')
        d.status = data.status
        if data.feedback is not None: d.feedback = data.feedback
        audit_commit(db, user.id, 'TEST_DRIVE_STATUS_CHANGED', f'{item_id}:{data.status}')
        db.refresh(d)
        return public_drive(d)

    @app.delete('/api/test-drives/{item_id}')
    def delete_drive(item_id: int, db=Depends(get_db), user=Depends(permission('ADMIN','MANAGER'))):
        d = get_required(db, TestDrive, item_id)
        db.delete(d)
        audit_commit(db, user.id, 'TEST_DRIVE_DELETED', str(item_id))
        return {'ok': True}

    @app.get('/api/dashboard')
    def dashboard(db=Depends(get_db), user=Depends(current_user)):
        counts = dict(db.execute(select(Vehicle.status, func.count(Vehicle.id)).group_by(Vehicle.status)).all())
        revenue = db.scalar(select(func.coalesce(func.sum(Sale.final_amount),0)).where(Sale.status=='COMPLETED'))
        completed = db.scalar(select(func.count(Sale.id)).where(Sale.status=='COMPLETED'))
        pending = db.scalar(select(func.count(Sale.id)).where(Sale.status=='PENDING'))
        upcoming_stmt = select(TestDrive).options(joinedload(TestDrive.vehicle), joinedload(TestDrive.customer), joinedload(TestDrive.salesperson)).where(TestDrive.status=='SCHEDULED', TestDrive.scheduled_at >= utcnow()).order_by(TestDrive.scheduled_at.asc()).limit(5)
        recent_stmt = select(Sale).options(joinedload(Sale.vehicle), joinedload(Sale.customer), joinedload(Sale.salesperson)).order_by(Sale.id.desc()).limit(5)
        showrooms = db.scalars(select(Showroom).order_by(Showroom.id)).all()
        by_showroom = [{'id':sh.id, 'name':sh.name, 'city':sh.city,
                        'total':db.scalar(select(func.count(Vehicle.id)).where(Vehicle.showroom_id==sh.id)),
                        'available':db.scalar(select(func.count(Vehicle.id)).where(Vehicle.showroom_id==sh.id, Vehicle.status=='AVAILABLE'))} for sh in showrooms]
        months = []
        today = date.today()
        for i in range(5,-1,-1):
            year = today.year
            month = today.month - i
            while month <= 0: month += 12; year -= 1
            prefix = f'{year}-{month:02d}'
            val = db.scalar(select(func.coalesce(func.sum(Sale.final_amount),0)).where(Sale.status=='COMPLETED', Sale.sale_date.like(prefix+'%')))
            months.append({'month':date(year,month,1).strftime('%b'), 'revenue':float(val)})
        return {'vehicles':sum(counts.values()), 'available':counts.get('AVAILABLE',0),
                'reserved':counts.get('RESERVED',0), 'sold':counts.get('SOLD',0),
                'inService':counts.get('IN_SERVICE',0), 'revenue':float(revenue),
                'completedSales':completed, 'pendingSales':pending,
                'customers':db.scalar(select(func.count(Customer.id))),
                'upcomingCount':db.scalar(select(func.count(TestDrive.id)).where(TestDrive.status=='SCHEDULED',TestDrive.scheduled_at>=utcnow())),
                'upcomingDrives':[public_drive(x) for x in db.scalars(upcoming_stmt).all()],
                'recentSales':[public_sale(x) for x in db.scalars(recent_stmt).all()],
                'showrooms':by_showroom, 'monthlyRevenue':months}

    @app.get('/api/audit')
    def audit(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
              db=Depends(get_db), user=Depends(permission('ADMIN'))):
        stmt = select(AuditEvent).order_by(AuditEvent.id.desc())
        return paginate(db, stmt, lambda a: {'id':a.id,'userId':a.user_id,'action':a.action,'target':a.target,'createdAt':a.created_at.isoformat()}, page, limit)

    frontend = ROOT / 'frontend'
    app.mount('/assets', StaticFiles(directory=frontend / 'assets'), name='assets')

    @app.get('/')
    def index(): return FileResponse(frontend / 'index.html')

    @app.get('/{path:path}')
    def fallback(path: str):
        if path.startswith('api/') or '.' in path: error(404,'Not found')
        return FileResponse(frontend / 'index.html')

    return app


app = create_app()
