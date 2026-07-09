import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"


def call_api(method, path, data=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers=headers,
        method=method.upper(),
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8")
            status_code = response.getcode()
            try:
                body = json.loads(content) if content else {}
            except json.JSONDecodeError:
                body = content
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        status_code = e.code
        try:
            body = json.loads(content) if content else {}
        except json.JSONDecodeError:
            body = content
    except Exception as e:
        status_code = None
        body = str(e)

    print(f"{method.upper()} {path} -> {status_code}")
    if isinstance(body, (dict, list)):
        print(json.dumps(body, indent=4))
    else:
        print(body)
    print("-" * 60)

    return status_code, body


def test_register(username, email, password, password_confirm=None, status="student"):
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "password_confirm": password_confirm or password,
        "status": status,
    }
    return call_api("post", "/api/auth/google/register/", payload)


def test_login(identifier, password):
    payload = {
        "username": identifier,
        "password": password,
    }
    return call_api("post", "/api/auth/login/", payload)


def test_complete_profile(token, username, status="student"):
    payload = {
        "username": username,
        "status": status,
    }
    return call_api("post", "/api/auth/google/complete-profile/", payload, token=token)


def test_google_login(id_token):
    payload = {"id_token": id_token}
    return call_api("post", "/api/auth/google/", payload)


def run_auth_flow(username, email, password, status="student"):
    print("Testing registration...")
    _, reg_body = test_register(username, email, password, status=status)

    print("Testing login...")
    _, login_body = test_login(username, password)

    if isinstance(login_body, dict):
        access_token = login_body.get("access")
    else:
        access_token = None

    if access_token:
        print("Testing profile completion...")
        test_complete_profile(access_token, username, status=status)
    else:
        print("No access token received; skipping profile completion test.")

def run_student_feedback_flow(token, feedback_data):
    print("Testing student feedback submission...")
    _, feedback_body = call_api("post", "/api/students/feedback-tracking/", feedback_data, token=token)

    if isinstance(feedback_body, dict):
        print("Feedback submission response:", feedback_body)
    else:
        print("Feedback submission failed or returned unexpected response.")


def run_student_feedback_get_flow(token):
    print("Testing student feedback retrieval...")
    _, feedback_list_body = call_api("get", "/api/students/feedback-tracking/", token=token)

    if isinstance(feedback_list_body, list):
        print("Feedback retrieval response:", feedback_list_body)
    else:
        print("Feedback retrieval failed or returned unexpected response.")

def test_admin_user_list(token=None):
    print("Testing Admin User List endpoint...")
    return call_api("get", "/api/auth/google/cred/all/", token=token)


def run_admin_endpoints_test():
    print("=== RUNNING ADMIN USER LIST TESTS ===")
    
    # 1. Unauthenticated test (should fail with 401 or 403)
    print("\n--- Test 1: Unauthenticated request (Expecting 401/403) ---")
    status_code, _ = test_admin_user_list(token=None)
    print(f"Status code received: {status_code} (Expected 401/403)")

    # 2. Non-admin test
    print("\n--- Test 2: Non-admin (Student) request (Expecting 403) ---")
    username_student = "test_student_user"
    email_student = "student_user@example.com"
    password = "StrongPass123!"
    
    status_code, login_body = test_login(username_student, password)
    if status_code != 200:
        print("Student not found, registering...")
        test_register(username_student, email_student, password, status="student")
        status_code, login_body = test_login(username_student, password)
        
    if status_code == 200:
        student_token = login_body.get("access")
        status_code, _ = test_admin_user_list(token=student_token)
        print(f"Status code received: {status_code} (Expected 403)")
    else:
        print("Failed to authenticate student, skipping non-admin test.")

    # 3. Admin test
    print("\n--- Test 3: Admin request (Expecting 200) ---")
    username_admin = "test_admin_user"
    email_admin = "admin_user@example.com"
    
    status_code, login_body = test_login(username_admin, password)
    if status_code != 200:
        print("Admin not found, registering...")
        test_register(username_admin, email_admin, password, status="admin")
        status_code, login_body = test_login(username_admin, password)
        
    if status_code == 200:
        admin_token = login_body.get("access")
        status_code, users = test_admin_user_list(token=admin_token)
        print(f"Status code received: {status_code} (Expected 200)")
        if status_code == 200:
            print(f"Successfully retrieved {len(users)} users.")
            print(f"Successfully retrieved users: {users}")
    else:
        print("Failed to authenticate admin, skipping admin test.")
    print("======================================")

def test_PO_KPI_list(token=None):
    print("Testing KPI List endpoint...")
    return call_api("get", "/api/analytics/kpis/", token=token)


def test_admin_KPI_post(data={}, token=None):
    print("Testing KPI List endpoint...")
    return call_api("post", "/api/analytics/kpis/", data=data, token=token)


def run_admin_KPI_endpoints_test():
    print("=== RUNNING ADMIN KPI ENDPOINTS TESTS ===")
    
    # 1. Unauthenticated test (should fail with 401 or 403)
    print("\n--- Test 1: Unauthenticated request (Expecting 401/403) ---")
    status_code, _ = test_admin_user_list(token=None)
    print(f"Status code received: {status_code} (Expected 401/403)")

    # 2. Non-admin test
    print("\n--- Test 2: Non-admin (Student) request (Expecting 403) ---")
    username_student = "test_student_user"
    email_student = "student_user@example.com"
    password = "StrongPass123!"

    data = {
        #'id', 'title', 'description', 'embedlink', 'metrics'
        'title': 'Test KPI',
        'description': 'This is a test KPI description.',
        'embedlink': 'https://example.com/kpi-embed',
        'metrics': {'metric1': 100, 'metric2': 200}
    }
    
    status_code, login_body = test_login(username_student, password)
    if status_code != 200:
        print("Student not found, registering...")
        test_register(username_student, email_student, password, status="student")
        status_code, login_body = test_login(username_student, password)
        
    if status_code == 200:
        student_token = login_body.get("access")
        status_code, _ = test_admin_KPI_post(data=data, token=student_token)
        print(f"Status code received: {status_code} (Expected 403)")
    else:
        print("Failed to authenticate student, skipping non-admin test.")

    # 3. Admin test
    print("\n--- Test 3: Admin request (Expecting 200) ---")
    username_admin = "test_admin_user"
    email_admin = "admin_user@example.com"
    
    status_code, login_body = test_login(username_admin, password)
    if status_code != 200:
        print("Admin not found, registering...")
        test_register(username_admin, email_admin, password, status="admin")
        status_code, login_body = test_login(username_admin, password)
        
    if status_code == 200:
        admin_token = login_body.get("access")
        status_code, Returns = test_admin_KPI_post(data=data, token=admin_token)
        print(f"Status code received: {status_code} (Expected 200)")
        if status_code == 200:
            # print(f"Successfully retrieved {len(Returns)} Returns.")
            print(f"Successfully retrieved Returns: {Returns}")
    else:
        print("Failed to authenticate admin, skipping admin test.")
    print("======================================")


def run_admin_PO_KPI_endpoints_test():
    print("=== RUNNING PO KPI ENDPOINTS TESTS ===")
    
    # 1. Unauthenticated test (should fail with 401 or 403)
    print("\n--- Test 1: Unauthenticated request (Expecting 401/403) ---")
    status_code, _ = test_PO_KPI_list(token=None)
    print(f"Status code received: {status_code} (Expected 401/403)")

    # 2. Non-admin test
    print("\n--- Test 2: Non-admin (Student) request (Expecting 403) ---")
    username_student = "test_student_user"
    email_student = "student_user@example.com"
    password = "StrongPass123!"
    
    status_code, login_body = test_login(username_student, password)
    if status_code != 200:
        print("Student not found, registering...")
        test_register(username_student, email_student, password, status="student")
        status_code, login_body = test_login(username_student, password)
        
    if status_code == 200:
        student_token = login_body.get("access")
        status_code, _ = test_PO_KPI_list(token=student_token)
        print(f"Status code received: {status_code} (Expected 403)")
    else:
        print("Failed to authenticate student, skipping non-admin test.")

    # 3. Admin test
    print("\n--- Test 3: Admin request (Expecting 200) ---")
    username_admin = "test_admin_user"
    email_admin = "admin_user@example.com"
    
    status_code, login_body = test_login(username_admin, password)
    if status_code != 200:
        print("Admin not found, registering...")
        test_register(username_admin, email_admin, password, status="admin")
        status_code, login_body = test_login(username_admin, password)
        
    if status_code == 200:
        admin_token = login_body.get("access")
        status_code, Returns = test_PO_KPI_list(token=admin_token)
        print(f"Status code received: {status_code} (Expected 200)")
        if status_code == 200:
            # print(f"Successfully retrieved {len(Returns)} Returns.")
            print(f"Successfully retrieved Returns: {Returns}")
    else:
        print("Failed to authenticate admin, skipping admin test.")
    print("======================================")


def test_update_post(data={}, token=None):
    print("Testing Update POST endpoint...")
    return call_api("post", "/api/updates/endpoints/", data=data, token=token)

def test_update_list(token=None):
    print("Testing Update GET endpoint...")
    return call_api("get", "/api/updates/endpoints/", token=token)

def run_update_endpoints_test():
    print("=== RUNNING UPDATE ENDPOINTS TESTS ===")
    
    password = "StrongPass123!"

    # 1. Non-admin (Student) test
    print("\n--- Test 1: Non-admin (Student) request ---")
    username_student = "test_student_user"
    email_student = "student_user@example.com"
    
    data = {
        'category': 'General',
        'title': 'Test Update',
        'description': 'This is a test update.',
        'classification': 'Info',
        'forUser': 'student',
        'button': {'label': 'Click Here', 'url': 'http://example.com'}
    }
    
    status_code, login_body = test_login(username_student, password)
    if status_code != 200:
        test_register(username_student, email_student, password, status="student")
        status_code, login_body = test_login(username_student, password)
        
    if status_code == 200:
        student_token = login_body.get("access")
        
        # Student POST (Should fail with 403)
        print(">> Student attempting POST (Expecting 403)")
        status_code, _ = test_update_post(data=data, token=student_token)
        print(f"Status code received: {status_code} (Expected 403)")
        
        # Student GET (Should succeed with 200)
        print(">> Student attempting GET (Expecting 200)")
        status_code, _ = test_update_list(token=student_token)
        print(f"Status code received: {status_code} (Expected 200)")
    else:
        print("Failed to authenticate student, skipping student test.")

    # 2. Admin test
    print("\n--- Test 2: Admin request ---")
    username_admin = "test_admin_user"
    email_admin = "admin_user@example.com"
    
    status_code, login_body = test_login(username_admin, password)
    if status_code != 200:
        test_register(username_admin, email_admin, password, status="admin")
        status_code, login_body = test_login(username_admin, password)
        
    if status_code == 200:
        admin_token = login_body.get("access")
        
        # Admin POST (Should succeed with 201)
        print(">> Admin attempting POST (Expecting 201)")
        status_code, returns = test_update_post(data=data, token=admin_token)
        print(f"Status code received: {status_code} (Expected 201)")
        
        # Admin GET (Should succeed with 200)
        print(">> Admin attempting GET (Expecting 200)")
        status_code, returns = test_update_list(token=admin_token)
        print(f"Status code received: {status_code} (Expected 200)")
        if status_code == 200:
            print(f"Successfully retrieved updates: {returns}")
    else:
        print("Failed to authenticate admin, skipping admin test.")
    print("======================================")

if __name__ == "__main__":
    # Run the new admin endpoints security test suite
    # run_admin_PO_KPI_endpoints_test()
    run_admin_KPI_endpoints_test()
