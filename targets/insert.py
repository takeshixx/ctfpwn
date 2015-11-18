#!/usr/bin/env python2
import sys
from pymongo import MongoClient

targets = [
'10.60.1.2',
'10.60.2.2',
'10.60.3.2',
'10.60.4.2',
'10.60.5.2',
'10.60.6.2',
'10.60.7.2',
'10.60.8.2',
'10.60.9.2',
'10.60.10.2',
'10.60.11.2',
'10.60.12.2',
'10.60.13.2',
'10.60.14.2',
'10.60.15.2',
'10.60.16.2',
'10.60.17.2',
'10.60.18.2',
'10.60.19.2',
'10.60.20.2',
'10.60.21.2',
'10.60.22.2',
'10.60.23.2',
'10.60.24.2',
'10.60.25.2',
'10.60.26.2',
'10.60.27.2',
'10.60.28.2',
'10.60.29.2',
'10.60.30.2',
'10.60.31.2',
'10.60.32.2',
'10.60.33.2',
'10.60.34.2',
'10.60.35.2',
'10.60.36.2',
'10.60.37.2',
'10.60.38.2',
'10.60.39.2',
'10.60.40.2',
'10.60.41.2',
'10.60.43.2',
'10.60.44.2',
'10.60.45.2',
'10.60.46.2',
'10.60.47.2',
'10.60.48.2',
'10.60.49.2',
'10.60.50.2',
'10.60.51.2',
'10.60.52.2',
'10.60.53.2',
'10.60.54.2',
'10.60.55.2',
'10.60.56.2',
'10.60.57.2',
'10.60.58.2',
'10.60.59.2',
'10.60.60.2',
'10.60.61.2',
'10.60.62.2',
'10.60.63.2',
'10.60.64.2',
'10.60.65.2',
'10.60.66.2',
'10.60.67.2',
'10.60.68.2',
'10.60.69.2',
'10.60.70.2',
'10.60.71.2',
'10.60.72.2',
'10.60.73.2',
'10.60.74.2',
'10.60.75.2',
'10.60.76.2',
'10.60.77.2',
'10.60.78.2',
'10.60.79.2',
'10.60.80.2',
'10.60.81.2',
'10.60.82.2',
'10.60.83.2',
'10.60.84.2',
'10.60.85.2',
'10.60.86.2',
'10.60.87.2',
'10.60.88.2',
'10.60.89.2',
'10.60.90.2',
'10.60.91.2',
'10.60.92.2',
'10.60.93.2',
'10.60.94.2',
'10.60.95.2',
'10.60.96.2',
'10.60.97.2',
'10.60.98.2',
'10.60.99.2',
'10.60.100.2',
'10.60.101.2',
'10.60.102.2',
'10.60.103.2',
'10.60.104.2',
'10.60.105.2',
'10.60.106.2',
'10.60.107.2',
'10.60.108.2',
'10.60.109.2',
'10.60.110.2',
'10.60.111.2',
'10.60.112.2',
'10.60.113.2',
'10.60.114.2',
'10.60.115.2',
'10.60.116.2',
'10.60.117.2',
'10.60.118.2',
'10.60.119.2',
'10.60.120.2',
'10.60.121.2',
'10.60.122.2',
'10.60.123.2',
'10.60.124.2',
'10.60.125.2',
'10.60.126.2',
'10.60.127.2',
'10.60.128.2',
'10.60.129.2',
'10.60.130.2',
'10.60.131.2',
'10.60.132.2',
'10.60.133.2',
'10.60.134.2',
'10.60.135.2',
'10.60.136.2',
'10.60.137.2',
'10.60.138.2',
'10.60.139.2',
'10.60.140.2',
'10.60.141.2',
'10.60.142.2',
'10.60.143.2',
'10.60.144.2',
'10.60.145.2',
'10.60.146.2',
'10.60.147.2',
'10.60.148.2',
'10.60.149.2',
'10.60.150.2',
'10.60.151.2',
'10.60.152.2',
'10.60.153.2',
'10.60.154.2',
'10.60.155.2',
'10.60.156.2',
'10.60.157.2',
'10.60.158.2',
'10.60.159.2',
'10.60.160.2',
'10.60.161.2',
'10.60.162.2',
'10.60.163.2',
'10.60.164.2',
'10.60.165.2',
'10.60.166.2',
'10.60.167.2',
'10.60.168.2',
'10.60.169.2',
'10.60.170.2',
'10.60.171.2',
'10.60.172.2',
'10.60.173.2',
'10.60.174.2',
'10.60.175.2',
'10.60.176.2',
'10.60.177.2',
'10.60.178.2',
'10.60.179.2',
'10.60.180.2',
'10.60.181.2',
'10.60.182.2',
'10.60.183.2',
'10.60.184.2',
'10.60.185.2',
'10.60.186.2',
'10.60.187.2',
'10.60.188.2',
'10.60.189.2',
'10.60.190.2',
'10.60.191.2',
'10.60.192.2',
'10.60.193.2',
'10.60.194.2',
'10.60.195.2',
'10.60.196.2',
'10.60.197.2',
'10.60.198.2',
'10.60.199.2',
'10.60.200.2',
'10.60.201.2',
'10.60.202.2',
'10.60.203.2',
'10.60.204.2',
'10.60.205.2',
'10.60.206.2',
'10.60.207.2',
'10.60.208.2',
'10.60.209.2',
'10.60.210.2',
'10.60.211.2',
'10.60.212.2',
'10.60.213.2',
'10.60.214.2',
'10.60.215.2',
'10.60.216.2',
'10.60.217.2',
'10.60.218.2',
'10.60.219.2',
'10.60.220.2',
'10.60.221.2',
'10.60.222.2',
'10.60.223.2',
'10.60.224.2',
'10.60.225.2',
'10.60.226.2',
'10.60.227.2',
'10.60.228.2',
'10.60.229.2',
'10.60.230.2',
'10.60.231.2',
'10.60.232.2',
'10.60.233.2',
'10.60.234.2',
'10.60.235.2',
'10.60.236.2',
'10.60.237.2',
'10.60.238.2',
'10.60.239.2',
'10.60.240.2',
'10.60.241.2',
'10.60.242.2',
'10.60.243.2',
'10.60.244.2',
'10.60.245.2',
'10.60.246.2',
'10.60.247.2',
'10.60.248.2',
'10.60.249.2',
'10.60.250.2',
'10.60.251.2',
'10.60.252.2',
'10.60.253.2',
'10.60.254.2',
'10.61.1.2',
'10.61.2.2',
'10.61.3.2',
'10.61.4.2',
'10.61.5.2',
'10.61.6.2',
'10.61.7.2',
'10.61.8.2',
'10.61.9.2',
'10.61.10.2',
'10.61.11.2',
'10.61.12.2',
'10.61.13.2',
'10.61.14.2',
'10.61.15.2',
'10.61.16.2',
'10.61.17.2',
'10.61.18.2',
'10.61.19.2',
'10.61.20.2',
'10.61.21.2',
'10.61.22.2',
'10.61.23.2',
'10.61.24.2',
'10.61.25.2',
'10.61.26.2',
'10.61.27.2',
'10.61.28.2',
'10.61.29.2',
'10.61.30.2',
'10.61.31.2',
'10.61.32.2',
'10.61.33.2',
'10.61.34.2',
'10.61.35.2',
'10.61.36.2',
'10.61.37.2',
'10.61.38.2',
'10.61.39.2',
'10.61.40.2',
'10.61.41.2',
'10.61.42.2',
'10.61.43.2',
'10.61.44.2',
'10.61.45.2',
'10.61.46.2',
'10.61.47.2',
'10.61.48.2',
'10.61.49.2',
'10.61.50.2',
'10.61.51.2',
'10.61.52.2',
'10.61.53.2',
'10.61.54.2',
'10.61.55.2',
'10.61.56.2',
'10.61.57.2',
'10.61.58.2',
'10.61.59.2',
'10.61.60.2',
'10.61.61.2',
'10.61.62.2',
'10.61.63.2',
'10.61.64.2',
'10.61.65.2',
'10.61.66.2',
'10.61.67.2',
'10.61.68.2',
'10.61.69.2',
'10.61.70.2',
'10.61.71.2',
'10.61.72.2',
'10.61.73.2',
'10.61.74.2',
'10.61.75.2',
'10.61.76.2',
'10.61.77.2',
'10.61.78.2',
'10.61.79.2',
'10.61.80.2',
'10.61.81.2',
'10.61.82.2',
'10.61.83.2',
'10.61.84.2',
'10.61.85.2',
'10.61.86.2',
'10.61.87.2',
'10.61.88.2',
'10.61.89.2',
'10.61.90.2',
'10.61.91.2',
'10.61.92.2',
'10.61.93.2',
'10.61.94.2',
'10.61.95.2',
'10.61.96.2',
'10.61.97.2',
'10.61.98.2',
'10.61.99.2',
'10.61.100.2',
'10.61.101.2',
'10.61.102.2',
'10.61.103.2',
'10.61.104.2',
'10.61.105.2',
'10.61.106.2',
'10.61.107.2',
'10.61.108.2',
'10.61.109.2',
'10.61.110.2',
'10.61.111.2',
'10.61.112.2',
'10.61.113.2',
'10.61.114.2',
'10.61.115.2',
'10.61.116.2',
'10.61.117.2',
'10.61.118.2',
'10.61.119.2',
'10.61.120.2',
'10.61.121.2',
'10.61.122.2',
'10.61.123.2',
'10.61.124.2',
'10.61.125.2',
'10.61.126.2',
'10.61.127.2',
'10.61.128.2',
'10.61.129.2',
'10.61.130.2',
'10.61.131.2',
'10.61.132.2',
'10.61.133.2',
'10.61.134.2',
'10.61.135.2',
'10.61.136.2',
'10.61.137.2',
'10.61.138.2',
'10.61.139.2',
'10.61.140.2',
'10.61.141.2',
'10.61.142.2',
'10.61.143.2',
'10.61.144.2',
'10.61.145.2',
'10.61.146.2',
'10.61.147.2',
'10.61.148.2',
'10.61.149.2',
'10.61.150.2',
'10.61.151.2',
'10.61.152.2',
'10.61.153.2',
'10.61.154.2',
'10.61.155.2',
'10.61.156.2',
'10.61.157.2',
'10.61.158.2',
'10.61.159.2',
'10.61.160.2',
'10.61.161.2',
'10.61.162.2',
'10.61.163.2',
'10.61.164.2',
'10.61.165.2',
'10.61.166.2',
'10.61.167.2',
'10.61.168.2',
'10.61.169.2',
'10.61.170.2',
'10.61.171.2',
'10.61.172.2',
'10.61.173.2',
'10.61.174.2',
'10.61.175.2',
'10.61.176.2',
'10.61.177.2',
'10.61.178.2',
'10.61.179.2',
'10.61.180.2',
'10.61.181.2',
'10.61.182.2',
'10.61.183.2',
'10.61.184.2',
'10.61.185.2',
'10.61.186.2',
'10.61.187.2',
'10.61.188.2',
'10.61.189.2',
'10.61.190.2',
'10.61.191.2',
'10.61.192.2',
'10.61.193.2',
'10.61.194.2',
'10.61.195.2',
'10.61.196.2',
'10.61.197.2',
'10.61.198.2',
'10.61.199.2',
'10.61.200.2',
'10.61.201.2',
'10.61.202.2',
'10.61.203.2',
'10.61.204.2',
'10.61.205.2',
'10.61.206.2',
'10.61.207.2',
'10.61.208.2',
'10.61.209.2',
'10.61.210.2',
'10.61.211.2',
'10.61.212.2',
'10.61.213.2',
'10.61.214.2',
'10.61.215.2',
'10.61.216.2',
'10.61.217.2',
'10.61.218.2',
'10.61.219.2',
'10.61.220.2',
'10.61.221.2',
'10.61.222.2',
'10.61.223.2',
'10.61.224.2',
'10.61.225.2',
'10.61.226.2',
'10.61.227.2',
'10.61.228.2',
'10.61.229.2',
'10.61.230.2',
'10.61.231.2',
'10.61.232.2',
'10.61.233.2',
'10.61.234.2',
'10.61.235.2',
'10.61.236.2',
'10.61.237.2',
'10.61.238.2',
'10.61.239.2',
'10.61.240.2',
'10.61.241.2',
'10.61.242.2',
'10.61.243.2'
]

if __name__ == '__main__':
    try:
        client = MongoClient()
        db = client.exploitservice
        col = db.targets
    except Exception as e:
        print(e)
        sys.exit(1)

    for target in targets:
        col.insert({'host': target, 'alive': True})

    print('Targets inserted')

