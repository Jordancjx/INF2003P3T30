var username_validated = true;
var fname_validated = true;
var lname_validated = true;
var email_validated = true;
var pwd_validated = true;
var pwd_confirm_validated = true;


const illegalCharacterRegex = /&(amp|lt|gt|quot|#39);/g;

function verifyUsername() {
     const username_input = document.getElementById("username");
     const usernameErrorMessageElement = document.getElementById("username-error-message");

     const sanitizedUsername = sanitizeInput(username_input.value);

     if (!sanitizedUsername.match(illegalCharacterRegex)) {
          usernameErrorMessageElement.textContent = "";
          username_validated = true;
     } else {
          usernameErrorMessageElement.textContent = "\u2022 Username contains illegal characters!";
          username_validated = false;
     }
}

function verifyFname() {
     const fname_input = document.getElementById("fname");
     const fnameErrorMessageElement = document.getElementById("fname-error-message");

     const sanitizedFname = sanitizeInput(fname_input.value);

     if (!sanitizedFname.match(illegalCharacterRegex)) {
          fnameErrorMessageElement.textContent = "";
          fname_validated = true;
     } else {
          fnameErrorMessageElement.textContent = "\u2022 First Name contains illegal characters!";
          fname_validated = false;
     }
}

function verifyLname() {
     const lname_input = document.getElementById("lname");
     const lnameErrorMessageElement = document.getElementById("lname-error-message");

     const sanitizedLname = sanitizeInput(lname_input.value);

     if (!sanitizedLname.match(illegalCharacterRegex)) {
          lnameErrorMessageElement.textContent = "";
          lname_validated = true;
     } else {
          lnameErrorMessageElement.textContent = "\u2022 Last Name contains illegal characters!";
          lname_validated = false;
     }
}

function verifyEmail() {
     const email_input = document.getElementById("email");
     const emailErrorMessageElement = document.getElementById("email-error-message");

     const sanitizedEmail = sanitizeInput(email_input.value);

     var emailRegex = /^(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$/i;

     if (sanitizedEmail.match(emailRegex)) {
          emailErrorMessageElement.textContent = "";
          email_validated = true;
     } else {
          emailErrorMessageElement.textContent = "\u2022 Invalid email address!";
          email_validated = false;
     }
     console.log("Email Check");
}

function verifyPassword() {
     const pwd_input = document.getElementById("pwd");
     const pwdErrorMessageElement = document.getElementById("pwd-error-message");

     const pwdValue = pwd_input.value;

     var passwordRegex = /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).+$/;

     if (pwdValue.match(passwordRegex)) {
          pwdErrorMessageElement.textContent = "";
          pwd_validated = true;
     } else {
          pwdErrorMessageElement.textContent = "\u2022 Password must contain at least 1 uppercase letter, 1 lowercase letter, and 1 number";
          pwd_validated = false;
     }
}

function verifyConfirmPassword() {
     const pwd_input = document.getElementById("pwd");
     const pwd_confirm_input = document.getElementById("pwd_confirm");

     const pwdConfirmErrorMessageElement = document.getElementById("pwd-confirm-error-message");

     if (pwd_input.value == pwd_confirm_input.value) {
          pwdConfirmErrorMessageElement.textContent = "";
          pwd_confirm_validated = true;
     } else {
          pwdConfirmErrorMessageElement.textContent = "\u2022 Passwords does not match!";
          pwd_confirm_validated = false;
     }
}

function sanitizeInput(data) {
     // Trim whitespace from the beginning and end of the string
     data = data.trim();

     // Remove backslashes
     data = data.replace(/\\/g, '');

     // Convert special characters to HTML entities
     data = data.replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;'); // or &apos; according to HTML5 specification

     return data;
}


document.getElementById("register_button").addEventListener("click", function (event) {
     if (!username_validated || !fname_validated || !lname_validated || !email_validated || !pwd_validated || !pwd_confirm_validated) {
          // Call your function here
          event.preventDefault();
     }
});