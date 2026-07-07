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
        print(json.dumps(body, indent=2))
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

if __name__ == "__main__":
    _, login_body = test_login(
        identifier="demo_user",
        password="StrongPass123!",
    )
    access_token = login_body.get("access") if isinstance(login_body, dict) else None

    if not access_token:
        raise SystemExit("No access token returned from login.")

    run_student_feedback_flow(
        token=access_token,
        feedback_data={
            "student": "demo_user",
            "student_email": "demo_user@example.com",
            "feedback": "This is a test feedback.",
            "category": "complaint",
            "urgency": "normal"
        }
    )

