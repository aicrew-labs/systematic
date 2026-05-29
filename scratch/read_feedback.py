import os, sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('.env')
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

if not url or not key:
    print('Supabase credentials not found.')
    sys.exit(1)

supabase = create_client(url, key)
res = supabase.table('app_users').select('user_id, feedback').execute()
for r in res.data:
    if r.get('feedback'):
        print(f"User {r['user_id']}:\n{r['feedback']}\n---")
