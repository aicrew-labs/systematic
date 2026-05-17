import requests
from bs4 import BeautifulSoup

session = requests.Session()
login_url = "https://systematic.ominfo.in/erp/crm_login.php"
payload = {
    "emailid": "SYS079",
    "psw": "5651"
}

print("Attempting login...")
res = session.post(login_url, data=payload, allow_redirects=True)

if res.status_code == 200:
    print("Login request completed.")
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Look for sidebar or nav menus
    nav = soup.find('nav')
    if nav:
        links = nav.find_all('a')
        print(f"Found {len(links)} navigation links.")
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href')
            if text and href and href != '#':
                print(f"- {text}: {href}")
    else:
        print("Could not find a <nav> element. Here are all links containing 'href':")
        links = soup.find_all('a', href=True)
        for link in links:
            print(f"- {link.get_text(strip=True)}: {link.get('href')}")
            
    # Try to find dashboard cards or modules
    print("\nPage title:", soup.title.string if soup.title else "No title")
else:
    print("Failed to login, status code:", res.status_code)
