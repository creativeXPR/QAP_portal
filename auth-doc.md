## HTMLs

- sign-in
```html
        <div id="email-section" class="login-section">
            <div class="form-group">
                <label for="identifier">Email or Username:</label>
                <input type="text" id="identifier" placeholder="Enter your email or username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" placeholder="Enter your password" required>
            </div>
            <button type="button" class="btn btn-primary" onclick="handleEmailLogin(event)">Sign In</button>
        </div>
```

- sign-up
```html
    <div id="register-section" class="login-section">
            <div class="form-group">
                <label for="reg-username">Username:</label>
                <input type="text" id="reg-username" placeholder="Choose a username" required>
            </div>
            <div class="form-group">
                <label for="reg-email">Email:</label>
                <input type="email" id="reg-email" placeholder="Enter your email" required>
            </div>
            <div class="form-group">
                <label for="reg-password">Password:</label>
                <input type="password" id="reg-password" placeholder="Enter a strong password" required>
            </div>
            <div class="form-group">
                <label for="reg-password-confirm">Confirm Password:</label>
                <input type="password" id="reg-password-confirm" placeholder="Confirm your password" required>
            </div>
            <div class="form-group">
                <label for="reg-status">University Status:</label>
                <select id="reg-status">
                    <option value="student">Student</option>
                    <option value="focal_person">Focal Person</option>
                    <option value="principle_officer">Principle Officer</option>
                    <option value="admin">Administrator</option>
                </select>
            </div>
            <button type="button" id="reg-submit" class="btn btn-primary" onclick="handleRegistration(event)">Create Account</button>
        </div>
```


- login link: 'http://127.0.0.1:8000/api/auth/login/'

```javascript
    try {
        const response = await fetch('http://127.0.0.1:8000/api/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: identifier,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            accessToken = data.access;
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);

            if (data.profile_complete === false) {
                localStorage.setItem('user_id', data.user_id);
                showProfileForm();
                showResult("Login successful! Please complete your profile.");
            } else {
                showResult(`✅ Welcome back, ${data.user.username}!`, false);
            }
        } else {
            showResult("Login failed: " + (data.error || "Invalid credentials"), true);
        }
    } catch (err) {
        showResult("Error connecting to backend: " + err.message, true);
        console.error(err);
    }
```

- registration link: 'http://127.0.0.1:8000/api/auth/google/register/'

```javascript
    try {
        alert("Sending registration request to backend...");
        const response = await fetch('http://127.0.0.1:8000/api/auth/google/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password,
                password_confirm: passwordConfirm,
                status: status
            })
        });

        alert("Registration response received.");
        console.log("Registration response received:", response);
        let data = null;
        try { data = await response.json(); } catch(e) { data = null; }
        alert("Registration data received.");
        if (response.ok) {
            alert("Registration successful!");
            console.log("Registration successful:", data);
            accessToken = data?.access;
            if (data?.access) localStorage.setItem('access_token', data.access);
            if (data?.refresh) localStorage.setItem('refresh_token', data.refresh);
            if (data?.user_id) localStorage.setItem('user_id', data.user_id);
            console.log("Account created successfully!");
            // Clear registration form
            document.getElementById('reg-username').value = '';
            document.getElementById('reg-email').value = '';
            document.getElementById('reg-password').value = '';
            document.getElementById('reg-password-confirm').value = '';
            console.log("Registration form cleared.");
            showResult(
                `✅ Account Created Successfully!<br>
                Username: <strong>${username}</strong><br>
                Status: <strong>${status}</strong><br>
                You are now logged in.`,
                false
            );
            console.log("Profile form submitted.");
        } else {
            // Build readable error message from returned JSON
            let msg = 'Unknown error';
            if (data) {
                if (typeof data === 'string') msg = data;
                else if (data.detail) msg = data.detail;
                else {
                    msg = Object.entries(data).map(([k, v]) => {
                        if (Array.isArray(v)) return `${k}: ${v.join(' ')}`;
                        if (typeof v === 'object') return `${k}: ${JSON.stringify(v)}`;
                        return `${k}: ${v}`;
                    }).join('<br>');
                }
            }
            showResult('Registration failed: ' + msg, true);
        }
    } catch (err) {
        showResult("Error creating account: " + err.message, true);
        console.error(err);
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = originalText; }
    }
```