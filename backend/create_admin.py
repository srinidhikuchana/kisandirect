"""Run with the backend stopped: python create_admin.py"""
import asyncio, getpass
from main import app, lifespan, mutate, uid, password_hash
async def main():
    name=input('Admin/FPO name: ').strip(); email=input('Email: ').strip().lower(); password=getpass.getpass('Password (12+ characters): ')
    if not name or '@' not in email or len(password)<12: raise SystemExit('Invalid name, email or password length.')
    async with lifespan(app):
        def create(s):
            if any(u['email']==email for u in s['users']): raise SystemExit('Email already exists.')
            s['users'].append({'id':uid(),'name':name,'email':email,'role':'admin','password':password_hash(password)})
        mutate(create)
    print('Admin created.')
asyncio.run(main())
