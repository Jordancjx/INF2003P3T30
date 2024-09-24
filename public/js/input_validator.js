function verifyEmail() {
     const email_input = document.getElementById("email");
     const emailErrorMessageElement = document.getElementById("email-error-message");

     const emailValue = email_input.value;
     const sanitizedEmail = sanitizeInput(emailValue);

     var emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
     var emailRegexV2 = /^(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$/i;

     if (sanitizedEmail.match(emailRegexV2)) {
          emailErrorMessageElement.textContent = "";
     } else {
          emailErrorMessageElement.textContent = "Invalid email address!";
     }
}

function verifyPassword() {
     const pwd_input = document.getElementById("pwd");
     const pwdErrorMessageElement = document.getElementById("pwd-error-message");

     const pwdValue = pwd_input.value;

     var passwordRegex = /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).+$/;

     if (pwdValue.match(passwordRegex)) {
          pwdErrorMessageElement.textContent = "";
     } else {
          pwdErrorMessageElement.textContent = "Password must contain at least 1 uppercase letter, 1 lowercase letter, and 1 number";
     }
}

function verifyConfirmPassword() {
     const pwd_input = document.getElementById("pwd");
     const pwd_confirm_input = document.getElementById("pwd_confirm");

     const pwdConfirmErrorMessageElement = document.getElementById("pwd-confirm-error-message");


     if (pwd_input.value == pwd_confirm_input.value) {
          pwdConfirmErrorMessageElement.textContent = "";
     } else {
          pwdConfirmErrorMessageElement.textContent = "Passwords does not match!";
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
