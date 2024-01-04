import requests
import time

# Base URL for the Maya node
ip_addresses = [
    "http://139.59.54.6",
    "http://45.76.183.136",
    "http://146.190.9.99",
    "http://95.216.138.145",
    "http://138.201.234.224",
    "http://139.59.52.149",
    "http://144.126.253.164",
    "http://139.59.54.247",
    "http://170.64.253.37",
    "http://212.95.53.168",
    "http://170.64.253.28",
    "http://139.84.192.232",
    "http://139.59.50.192",
    "http://138.201.234.225",
    "http://37.27.15.96",
    "http://174.138.121.14",
    "http://64.225.85.151",
    "http://138.201.234.226",
    "http://138.201.234.228",
    "http://54.212.187.67",
    "http://138.201.234.227",
    "http://95.217.214.92",
    "http://207.148.74.30",
    "http://170.64.253.51"
]


# ip_addresses = [
#     "http://170.64.253.28",
#     "http://170.64.253.37",
#     "http://170.64.253.40",
#     "http://138.201.234.228",
#     "http://212.95.53.168"
# ]

ip_addresses = ["https://midgard.mayachain.info"]

# Different endpoints to make requests to
# endpoints = [
#     ":1317/mayachain/pools"]
endpoints = [
    "/mayachain/pools"]
# Function to make a request to a given URL with a timeout and measure the time taken
def make_request_and_measure_time(ip, endpoint, timeout=1):  # Set a timeout of 5 seconds
    full_url = ip + endpoint
    start_time = time.time()
    try:
        response = requests.get(full_url, timeout=timeout)
        status_code = response.status_code
    except requests.exceptions.RequestException as e:
        return endpoint, 0, "Failed", str(e)
    end_time = time.time()
    elapsed_time = end_time - start_time
    return ip, endpoint, elapsed_time, "Success", status_code

# Making requests and measuring time for each endpoint
results = []

for ip in ip_addresses:
    for endpoint in endpoints:
        result = make_request_and_measure_time(ip, endpoint)
        results.append(result)

print(results)
