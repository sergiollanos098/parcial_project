# ingest.py - simple pull from an API endpoint and save to CSV + (optional) upload to S3 using boto3
import requests, csv, os
API = os.environ.get('API','http://ms1_flask:5001/users')
OUT = os.environ.get('OUT','/data/out.csv')
def run():
    r = requests.get(API).json()
    keys = list(r[0].keys()) if r else []
    with open(OUT,'w',newline='',encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in r:
            w.writerow(row)
    print('wrote',OUT)
if __name__=='__main__':
    run()
