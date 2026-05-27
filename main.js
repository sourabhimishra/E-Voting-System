// Validate password during registration
function validatePassword() {
    const password = document.getElementById("password").value;

    // Password rules
    if (password.length < 8) {
        alert("Password must be at least 8 characters long");
        return false;
    }
    if (!/[A-Z]/.test(password)) {
        alert("Password must contain at least one capital letter");
        return false;
    }
    if (!/[a-z]/.test(password)) {
        alert("Password must contain at least one small letter");
        return false;
    }
    if (!/[0-9]/.test(password)) {
        alert("Password must contain at least one number");
        return false;
    }
    if (!/[!@#$%^&*]/.test(password)) {
        alert("Password must contain at least one special character");
        return false;
    }

    return true; // allow form submit
}

// Validate voting (only one party must be selected)
function validateVote() {
    const parties = document.getElementsByName("party");

    for (let i = 0; i < parties.length; i++) {
        if (parties[i].checked) {
            return true; // one party selected
        }
    }

    alert("Please select a party before submitting your vote");
    return false;
}
