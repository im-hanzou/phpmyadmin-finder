#!/usr/bin/python
import sys
import time
import os
import pycurl
from io import BytesIO
import multiprocessing
from multiprocessing.pool import ThreadPool
from colorama import init, Fore, Style
import threading

init()

lock = threading.Lock()
found_count = 0

def display_banner():
    banner = f'''
 *   *__                  *   *     
| | / (_)                | | | |    
| |/ / * *__ *_*   ** *****| |*****| |**  
|    \\| | '__| '_ \\ / *` | *_| '_ \\ 
| |\\  \\ | |  | | | | (_| | |_| | | |
\\_| \\_/_|_|  |_| |_|\\__,_|\\__|_| |_|
                       ZeroByte.ID
'''
    print(Fore.RED + banner + Style.RESET_ALL)

def save_result(url):
    global found_count
    output_file = "successful_phpmyadmin.txt"
    with lock:
        with open(output_file, 'a') as f:
            f.write(f"{url}\n")
        found_count += 1
        print(Fore.GREEN + f"[+] Result saved to {output_file} (Total found: {found_count})" + Style.RESET_ALL)

def check_url(args):
    url, path = args
    buffer = BytesIO()
    c = pycurl.Curl()
    
    full_url = f'{url}{path}'
    
    c.setopt(c.URL, full_url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.SSL_VERIFYPEER, 0)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.USERAGENT, 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1')
    c.setopt(c.TIMEOUT, 10)
    
    try:
        c.perform()
        status_code = c.getinfo(c.RESPONSE_CODE)
        
        if status_code == 200:
            response_content = buffer.getvalue().decode('utf-8', errors='ignore')
            
            phpmyadmin_indicators = [
                '<title>phpMyAdmin</title>',
                '<input type="text" name="pma_username" id="input_username"'
            ]
            
            is_phpmyadmin = any(indicator in response_content for indicator in phpmyadmin_indicators)
            
            if is_phpmyadmin:
                print(Fore.GREEN + f"[+] Yeay! Found phpMyAdmin!\n[+] {full_url}" + Style.RESET_ALL)
                c.close()
                save_result(full_url)
                return full_url
            else:
                print(Fore.YELLOW + f"[!] {full_url} returns 200 but doesn't contain phpMyAdmin" + Style.RESET_ALL)
                c.close()
                return None
        else:
            print(Fore.RED + f"[!] {full_url} Not Found! (Status: {status_code})" + Style.RESET_ALL)
            c.close()
            return None
    except Exception as e:
        print(Fore.RED + f"[!] Error checking {full_url}: {e}" + Style.RESET_ALL)
        return None

def main():
    display_banner()
    
    url_file = str(input(Fore.YELLOW + "[+] Enter file containing URLs (one per line): " + Style.RESET_ALL))
    if not os.path.exists(url_file):
        print(Fore.RED + f"[!] File {url_file} not found!" + Style.RESET_ALL)
        sys.exit(1)
    
    with open(url_file, 'r') as f:
        urls = [url.strip() for url in f.readlines() if url.strip()]
    
    paths_file = 'data.txt'
    if not os.path.exists(paths_file):
        print(Fore.RED + f"[!] File {paths_file} not found!" + Style.RESET_ALL)
        sys.exit(1)
    
    with open(paths_file, 'r') as f:
        paths = [path.strip() for path in f.readlines() if path.strip()]
    
    print(Fore.GREEN + f"[+] Processing {len(urls)} URLs with {len(paths)} paths" + Style.RESET_ALL)
    time.sleep(1)
    
    tasks = []
    for url in urls:
        for path in paths:
            tasks.append((url, path))
    
    num_threads = 50
    print(Fore.GREEN + f"[+] Starting scan with {num_threads} threads" + Style.RESET_ALL)
    
    pool = ThreadPool(processes=num_threads)
    results = pool.map(check_url, tasks)
    pool.close()
    pool.join()
    
    successful = [r for r in results if r]
    
    if successful:
        print(Fore.GREEN + f"[+] Scan completed: Found {len(successful)} valid phpMyAdmin URLs." + Style.RESET_ALL)
    else:
        print(Fore.RED + "[!] No valid phpMyAdmin instances found." + Style.RESET_ALL)
    
    print(Fore.GREEN + "[+] Job Done! Scanning completed." + Style.RESET_ALL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n[!] Process interrupted by user. Exiting..." + Style.RESET_ALL)
        sys.exit(0)
