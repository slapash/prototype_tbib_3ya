const API_BASE_URL = "http://127.0.0.1:8000";

document.getElementById("register-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const first_name = document.getElementById("first_name").value;
    const last_name = document.getElementById("last_name").value;
    const phone_number = document.getElementById("phone_number").value;
    const user_type = document.getElementById("user_type").value;

    const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password, first_name, last_name, phone_number, user_type })
    });

    const user = await response.json();

    // Add the new user to the user list
    const userList = document.getElementById("user-list");
    const newUserItem = document.createElement("li");
    newUserItem.textContent = `${user.first_name} ${user.last_name} (${user.email})`;
    userList.appendChild(newUserItem);

    // Reset the form
    document.getElementById("register-form").reset();
});

document.getElementById("get-users").addEventListener("click", async () => {
    const response = await fetch(`${API_BASE_URL}/users`);

    const users = await response.json();

    // Clear the user list
    const userList = document.getElementById("user-list");
    userList.innerHTML = "";

    // Add each user to the user list
    users.forEach(user => {
        const userItem = document.createElement("li");
        userItem.textContent = `${user.first_name} ${user.last_name} (${user.email})`;
        userList.appendChild(userItem);
    });
});
document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    // Check if the login was successful
    if (data.token) {
        // Save the token in local storage
        localStorage.setItem("token", data.token);

        // Hide the login form and show the other content
        document.getElementById("login").style.display = "none";
        document.getElementById("register").style.display = "none";
        document.getElementById("users").style.display = "block";
        document.getElementById("schedules").style.display = "block";
    } else {
        alert("Invalid email or password.");
    }

    // Reset the form
    document.getElementById("login-form").reset();
});
