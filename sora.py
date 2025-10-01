import random
import string
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, CancelledError
import requests
import json
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def load_all_configs() -> dict:
    """Load all configurations from config.txt and params.txt"""
    all_configs = {}
    
    # Load browser configs
    config_files = {'config.txt': {}, 'params.txt': {}}
    for file_name, config_dict in config_files.items():
        if not os.path.exists(file_name):
            if file_name == 'config.txt':
                print(f"ERROR: Configuration file {file_name} not found.")
            continue
        
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Try to parse as int or float, otherwise keep as string
                        try:
                            value = int(value)
                        except ValueError:
                            try:
                                value = float(value)
                            except ValueError:
                                pass # Keep as string
                        config_dict[key.strip()] = value
            all_configs.update(config_dict)
        except Exception as e:
            print(f"Error reading configuration file {file_name}: {e}")
            
    return all_configs


def generate_invite_code() -> str:
    """Generate 6-character invite code: starts with 0, then letter, then alternating digits/letters"""
    chars = ['0']  # First position fixed as 0
    chars.append(random.choice(string.ascii_uppercase))
    for i in range(4):
        if i % 2 == 0:
            chars.append(random.choice(string.digits.replace('0', '')))
        else:
            chars.append(random.choice(string.ascii_uppercase))
    return ''.join(chars)


def sanitize_auth_token(token: str) -> str:
    """Replace problematic non-ASCII characters in the auth token with ASCII equivalents."""
    if not token:
        return token
    original_token = token
    replacements = {'…': '...', '"': '"', '"': '"', ''': "'", ''': "'", '–': '-', '—': '--',}
    for unicode_char, ascii_replacement in replacements.items():
        if unicode_char in token:
            token = token.replace(unicode_char, ascii_replacement)
            print(f"INFO: Replaced character '{unicode_char}' with '{ascii_replacement}' in auth token.")
    try:
        token.encode('ascii')
    except UnicodeEncodeError:
        print("WARNING: Auth token contains other non-ASCII characters. Replacing them with '?'.")
        token = token.encode('ascii', errors='replace').decode('ascii')
    if token != original_token:
        print("INFO: Auth token has been sanitized to be ASCII-safe.")
    return token


def load_auth_token() -> str:
    """Load authentication token from auth.txt file"""
    try:
        possible_paths = ['auth.txt']
        auth_token = ""
        for path in possible_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    auth_token = f.read().strip()
                    break
            except FileNotFoundError:
                continue
        if not auth_token:
            print("ERROR: auth.txt file not found")
            return ""
        if auth_token.startswith('Bearer '):
            auth_token = auth_token[7:].strip()
        auth_token = ''.join(auth_token.split())
        if not auth_token:
            print("ERROR: auth.txt file is empty")
            return ""
        auth_token = sanitize_auth_token(auth_token)
        return auth_token
    except UnicodeDecodeError:
        print("ERROR: auth.txt file encoding incorrect, ensure it's UTF-8")
        return ""
    except Exception as e:
        print(f"Error reading auth.txt: {e}")
        return ""


def load_used_codes(file_path: str = "used_codes.txt") -> set:
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        print(f"Error reading used codes file: {e}")
        return set()


def load_invalid_codes(file_path: str = "invalid_codes.txt") -> set:
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        print(f"Error reading invalid codes file: {e}")
        return set()


def save_used_code(code: str, file_path: str = "used_codes.txt"):
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{code}\n")
    except Exception as e:
        print(f"Error saving invite code: {e}")


def save_success_code(code: str, file_path: str = "success.txt"):
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{code}\n")
    except Exception as e:
        print(f"Error saving success code: {e}")


def save_invalid_code(code: str, file_path: str = "invalid_codes.txt"):
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{code}\n")
    except Exception as e:
        print(f"Error saving invalid code: {e}")


def safe_print(text: str):
    """Safely print text that might contain non-ASCII characters"""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            safe_text = text.encode('ascii', errors='replace').decode('ascii')
            print(safe_text)
        except:
            print("Print error occurred")
    except Exception as e:
        print(f"Printing error: {e}")


class UTF8HTTPAdapter(HTTPAdapter):
    """Custom HTTP adapter that forces UTF-8 encoding for responses"""
    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        if response.encoding is None or response.encoding.lower() in ['iso-8859-1', 'latin-1']:
            response.encoding = 'utf-8'
        return response


def submit_invite_code(invite_code: str, auth_token: str, config: dict, max_retries: int, retry_delay: float) -> tuple[str, bool, str]:
    """Submit single invite code, retry until success or max retries reached"""
    url = "https://sora.chatgpt.com/backend/project_y/invite/accept"
    headers = {
        'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-GB,en;q=0.5',
        'Authorization': f'Bearer {auth_token}', 'Connection': 'keep-alive', 'Content-Type': 'application/json',
        'Host': 'sora.chatgpt.com', 'OAI-Device-Id': config.get('OAI-Device-Id', ''), 'Priority': 'u=4',
        'Referer': 'https://sora.chatgpt.com/explore', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin', 'User-Agent': config.get('User-Agent', ''),
    }
    data = {"invite_code": invite_code}
    json_payload_bytes = json.dumps(data).encode('utf-8')

    for attempt in range(max_retries):
        try:
            session = requests.Session()
            session.mount('https://', UTF8HTTPAdapter())
            response = session.post(url, headers=headers, data=json_payload_bytes, timeout=None)
            
            if response.status_code == 200:
                safe_print(f"[SUCCESS] Code {invite_code} submitted successfully!")
                return ("success", True, invite_code)
            elif response.status_code == 401:
                safe_print(f"[AUTH_ERROR] Code {invite_code} failed: Authentication token is invalid or expired (401).")
                return ("auth_error", False, invite_code)
            elif response.status_code == 403:
                safe_print(f"[INVALID_CODE] Code {invite_code} is invalid, need to replace")
                return ("invalid_code", False, invite_code)
            elif response.status_code == 429:
                safe_print(f"[RATE_LIMITED] Code {invite_code} rate limited, retrying... (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    safe_print(f"[RATE_LIMITED] Code {invite_code} still rate limited after {max_retries} retries, giving up")
                    return ("rate_limited_max", False, invite_code)
            else:
                safe_print(f"[ERROR] Code {invite_code} returned status code: {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    safe_print(f"[ERROR] Code {invite_code} still failed after {max_retries} retries, giving up")
                    return ("error_max", False, invite_code)
        except requests.exceptions.RequestException as e:
            safe_print(f"[REQUEST_ERROR] Code {invite_code} request error, retrying...: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                safe_print(f"[REQUEST_ERROR] Code {invite_code} still failed after {max_retries} retries, giving up")
                return ("request_error_max", False, invite_code)
        except Exception as e:
            error_type = type(e).__name__
            error_details = str(e)
            safe_print(f"[UNEXPECTED_ERROR] Code {invite_code} - {error_type}: {error_details}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                safe_print(f"[UNEXPECTED_ERROR] Code {invite_code} still failed after {max_retries} retries, giving up")
                return ("unexpected_error_max", False, invite_code)
    return ("max_retries_exceeded", False, invite_code)


def worker(invite_code: str, auth_token: str, config: dict, used_codes: set, lock: threading.Lock, max_retries: int, retry_delay: float) -> tuple[str, bool, str]:
    try:
        with lock:
            if invite_code in used_codes:
                return ("duplicate", False, invite_code)
            used_codes.add(invite_code)
        
        result, success, code = submit_invite_code(invite_code, auth_token, config, max_retries, retry_delay)
        
        if success:
            with lock:
                save_used_code(invite_code)
                save_success_code(invite_code)
        else:
            with lock:
                used_codes.discard(invite_code)
                if result == "invalid_code":
                    save_invalid_code(invite_code)
        
        return (result, success, invite_code)
    
    except Exception as e:
        error_type = type(e).__name__
        error_details = str(e)
        error_msg = f"Worker thread error for code {invite_code}: {error_type}: {error_details}"
        try:
            safe_print(error_msg)
        except Exception as print_error:
            print(f"Worker thread error for code {invite_code} - Type: {error_type}. Could not print details.")
        return ("worker_error", False, invite_code)


def submit_invite_codes(config: dict) -> None:
    """Main function: infinitely generate and submit invite codes"""
    # Get parameters from config, with defaults
    max_workers = config.get('max_workers', 3)
    delay = config.get('delay', 3.0)
    max_retries = config.get('max_retries', 20)
    retry_delay = config.get('retry_delay', 8.0)
    used_codes_file = config.get('used_codes_file', "used_codes.txt")
    success_file = config.get('success_file', "success.txt")
    invalid_codes_file = config.get('invalid_codes_file', "invalid_codes.txt")

    if not config.get('OAI-Device-Id') or not config.get('User-Agent'):
        print("ERROR: config.txt is missing OAI-Device-Id or User-Agent. Please check the configuration file.")
        return

    print("Loading authentication token...")
    auth_token = load_auth_token()
    if not auth_token:
        print("Cannot get authentication token, please check auth.txt file")
        return
    
    used_codes = load_used_codes(used_codes_file)
    invalid_codes = load_invalid_codes(invalid_codes_file)
    lock = threading.Lock()
    
    print("Starting infinite invite code generation and submission...")
    print(f"Threads: {max_workers}, Delay: {delay}s, Max retries: {max_retries}, Retry delay: {retry_delay}s")
    print(f"Used codes: {len(used_codes)}, Known invalid codes: {len(invalid_codes)}")
    print("Press Ctrl+C to stop")
    
    start_time = time.time()
    last_success_count = 0
    results = {"success": 0, "failed": 0, "duplicate": 0, "invalid_code": 0, "rate_limited": 0, "error": 0, "request_error": 0, "rate_limited_max": 0, "error_max": 0, "request_error_max": 0, "worker_error": 0, "unexpected_error_max": 0, "encoding_error_max": 0, "auth_error": 0}
    processed_codes = 0
    
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            invite_codes = []
            for _ in range(max_workers * 2):
                code = generate_invite_code()
                with lock:
                    while code in used_codes or code in invalid_codes:
                        code = generate_invite_code()
                invite_codes.append(code)
            
            print(f"Generated initial batch of {len(invite_codes)} invite codes")
            future_to_code = {executor.submit(worker, code, auth_token, config, used_codes, lock, max_retries, retry_delay): code for code in invite_codes}
            
            while future_to_code:
                for future in as_completed(future_to_code):
                    try:
                        result, success, code = future.result()
                        del future_to_code[future]
                        processed_codes += 1
                        results[result] = results.get(result, 0) + 1
                        
                        if result == "auth_error":
                            safe_print("FATAL: Authentication failed. Stopping all threads. Please update your auth token.")
                            for f in future_to_code:
                                f.cancel()
                            break
                        
                        if success:
                            results["success"] += 1
                            current_success = results["success"]
                            if current_success % 10 == 0 and current_success != last_success_count:
                                safe_print(f"[PROGRESS] Successfully submitted {current_success} invite codes")
                                last_success_count = current_success
                        elif result == "invalid_code":
                            with lock:
                                invalid_codes.add(code)
                            safe_print(f"[INVALID] Code {code} is invalid, recorded")
                            results["invalid_code"] += 1
                            new_code = generate_invite_code()
                            with lock:
                                while new_code in used_codes or new_code in invalid_codes:
                                    new_code = generate_invite_code()
                            safe_print(f"[REPLACE] Replacing invalid code {code} with new code {new_code}")
                            new_future = executor.submit(worker, new_code, auth_token, config, used_codes, lock, max_retries, retry_delay)
                            future_to_code[new_future] = new_code
                        elif result in ["rate_limited_max", "error_max", "request_error_max", "worker_error", "unexpected_error_max", "encoding_error_max"]:
                            safe_print(f"[GIVE_UP] Code {code} reached max retries, giving up")
                            with lock:
                                used_codes.discard(code)
                            results[result] += 1
                            new_code = generate_invite_code()
                            with lock:
                                while new_code in used_codes or new_code in invalid_codes:
                                    new_code = generate_invite_code()
                            safe_print(f"[REPLACE] Replacing abandoned code {code} with new code {new_code}")
                            new_future = executor.submit(worker, new_code, auth_token, config, used_codes, lock, max_retries, retry_delay)
                            future_to_code[new_future] = new_code
                        else:
                            results["failed"] += 1
                        
                        if delay > 0:
                            time.sleep(delay)
                    
                    except CancelledError:
                        pass
                    except Exception as e:
                        error_type = type(e).__name__
                        error_details = str(e)
                        error_message = f"Thread execution error: {error_type}: {error_details}"
                        try:
                            safe_print(error_message)
                        except Exception as print_error:
                            print(f"A thread execution error occurred ({error_type}). Could not print details due to a printing error.")
                        results["error"] += 1
                        processed_codes += 1
    
    except KeyboardInterrupt:
        print("\n\nInterrupt signal detected, stopping...")
    
    end_time = time.time()
    print("\n====== Program Stopped ======")
    print(f"Total runtime: {end_time - start_time:.2f} seconds")
    print(f"Success: {results['success']}, Failed: {results['failed']}, Duplicate: {results['duplicate']}")
    print(f"Invalid codes: {results['invalid_code']}, Rate limited: {results['rate_limited']}, Errors: {results['error']}")
    print(f"Request errors: {results['request_error']}, Worker errors: {results['worker_error']}, Auth errors: {results['auth_error']}")
    print(f"Total processed codes: {processed_codes}")
    print(f"Success codes saved to: {success_file}, Used codes saved to: {used_codes_file}, Invalid codes saved to: {invalid_codes_file}")


def test_invite_code_format():
    print("Generating 10 test invite codes:")
    for i in range(10):
        code = generate_invite_code()
        print(f"{i+1:2d}: {code}")
        assert len(code) == 6 and code[0] == '0' and code[1].isalpha() and code[1].isupper()
        for j in range(2, 6):
            if j % 2 == 0: assert code[j].isdigit()
            else: assert code[j].isalpha() and code[j].isupper()
        print("    OK Format correct")


if __name__ == "__main__":
    if sys.platform.startswith('win'):
        try:
            import os
            os.system('chcp 65001 >nul')
        except:
            pass
    
    test_invite_code_format()
    print("\n" + "="*50 + "\n")
    
    configs = load_all_configs()
    submit_invite_codes(configs)