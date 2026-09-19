import os, tempfile
os.environ['DATA_FILE']=tempfile.mktemp(suffix='.json')
os.environ['DEMO_MODE']='true'
os.environ['STORAGE']='json'
from fastapi.testclient import TestClient
from main import app, FILE

def test_end_to_end():
    with TestClient(app) as c:
        def auth(role):
            return {'Authorization':'Bearer '+c.post('/api/auth/demo/'+role).json()['token']}
        buyer,farmer,admin=auth('buyer'),auth('farmer'),auth('admin')
        listing=c.get('/api/listings').json()[0]
        from datetime import date
        body={'listing_id':listing['id'],'quantity':10,'address':'Test buyer, Hyderabad','lat':17.45,'lon':78.48,'delivery_date':str(date.today())}
        assert c.post('/api/orders',json=body,headers=farmer).status_code==403
        r=c.post('/api/orders',json=body,headers=buyer); assert r.status_code==201,r.text
        oid=r.json()['id']
        assert c.get('/api/listings').json()[0]['quantity']==listing['quantity']-10
        assert c.post('/api/orders',json=body|{'quantity':100000},headers=buyer).status_code==409
        assert c.post('/api/orders/'+oid+'/status',json={'status':'delivered'},headers=farmer).status_code==409
        assert c.post('/api/orders/'+oid+'/status',json={'status':'accepted'},headers=buyer).status_code==403
        assert c.post('/api/orders/'+oid+'/status',json={'status':'accepted'},headers=farmer).status_code==200
        assert c.get('/api/aggregation',headers=buyer).status_code==403
        assert c.get('/api/aggregation',headers=admin).json()[0]['kg']==10
        route=c.post('/api/routes',headers=admin,json={'delivery_date':str(date.today()),'capacity_kg':10,'vehicles':1})
        assert route.status_code==200,route.text
        stops=route.json()['routes'][0]['stops']; assert [s['change_kg'] for s in stops]==[0,10,-10,0]
        assert c.post('/api/routes',headers=admin,json={'delivery_date':str(date.today()),'capacity_kg':9,'vehicles':1}).status_code==422
        assert c.post('/api/orders/'+oid+'/status',json={'status':'cancelled'},headers=buyer).status_code==200
        assert c.get('/api/listings').json()[0]['quantity']==listing['quantity']
        assert c.post('/api/orders/'+oid+'/status',json={'status':'cancelled'},headers=buyer).status_code==409
        assert not c.get('/api/forecast',headers=farmer).json()['ready']
        assert c.post('/api/auth/register',json={'email':'new@test.local','password':'testing123','name':'New Buyer','role':'admin'}).status_code==422
        new=c.post('/api/auth/register',json={'email':'new@test.local','password':'testing123','name':'New Buyer','role':'buyer'})
        assert new.status_code==200
        assert c.get('/api/orders',headers={'Authorization':'Bearer '+new.json()['token']}).json()==[]
        assert c.get('/api/orders').status_code==401
    FILE.unlink(missing_ok=True)

def test_forecast_with_history():
    from main import mutate
    from datetime import date,timedelta
    with TestClient(app) as c:
        def populate(s):
            for i in range(21):
                d=str(date.today()-timedelta(days=20-i))
                s['orders'].append({'crop':'Tomato','status':'delivered','created_at':d+'T10:00:00+00:00','quantity':20+i,'total':(20+i)*25})
        mutate(populate)
        token=c.post('/api/auth/demo/farmer').json()['token']
        r=c.get('/api/forecast?crop=Tomato',headers={'Authorization':'Bearer '+token})
        assert r.status_code==200,r.text
        f=r.json(); assert f['ready']; assert len(f['forecast'])==7
        assert f['price_baseline']==25; assert all(d['kg']>=0 for d in f['forecast'])
    FILE.unlink(missing_ok=True)
