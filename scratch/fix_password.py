import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
supabase = create_client(url, key)

hashed = '$2b$12$Tat/qDaIOcFZB1T./Eaeee4i0vQdN9djCzAKQtkT1m/46V6e18i76'
res = supabase.table('app_users').update({'password': hashed}).eq('user_id', 'admin').execute()
print('Update Result:', res.data)
