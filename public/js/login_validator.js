var email_validated = true;

function verifyEmail() {
     const email_input = document.getElementById("email");
     const emailErrorMessageElement = document.getElementById("email-error-message");

     const emailValue = email_input.value;
     const sanitizedEmail = sanitizeInput(emailValue);

     var emailRegex = /^(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$/i;

     if (sanitizedEmail.match(emailRegex)) {
          emailErrorMessageElement.textContent = "";
          email_validated = true;
     } else {
          emailErrorMessageElement.textContent = "\u2022 Invalid email address!";
          email_validated = false;
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

document.getElementById("login_button").addEventListener("click", function (event) {
     if (!email_validated) {
          event.preventDefault();
     }
});
