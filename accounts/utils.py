import random
import string
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from django.core.mail import EmailMultiAlternatives



def generate_password(length=10):

    characters = (
        string.ascii_letters +
        string.digits +
        "@#$%!"
    )

    return "".join(
        random.choice(characters)
        for _ in range(length)
    )





def send_welcome_email(user, password):

    subject = "Welcome to HelpDesk Pro"

    html_content = f"""
    <html>

    <body style="font-family: Arial, Helvetica, sans-serif;
                 font-size:15px;
                 color:#333333;
                 line-height:1.7;">

        <p>Hi {user.first_name or user.email},</p>

        <p>
            Welcome to <strong>HelpDesk Pro</strong> 👋
        </p>

        <p>
            Your account has been created successfully by the
            <strong>System Administrator</strong>.
        </p>

        <p>
            Please use the following credentials to log in to your account.
        </p>

        <p>

            <strong>Login Details</strong>

            <br><br>

            <strong>Email:</strong>
            {user.email}
            
            <br>
             
            <strong>Username:</strong>
            {user.username}
            
            <br>

            <strong>Temporary Password:</strong>
            {password}

        </p>

        <p>
            For security reasons, we recommend changing your password after logging in.
        </p>

        
        <p>
            If you have any issues accessing your account,
            please contact your HelpDesk Administrator.
        </p>

        <br>

        <p>

            Regards,<br>

            <strong>HelpDesk Pro Team</strong>

        </p>

    </body>

    </html>
    """

    email = EmailMultiAlternatives(

        subject=subject,

        body="Please use an HTML supported email client.",

        from_email=settings.DEFAULT_FROM_EMAIL,

        to=[user.email],

    )

    email.attach_alternative(
        html_content,
        "text/html"
    )

    email.send()


def generate_username(email):

    base = email.split("@")[0].lower()

    while True:

        username = f"{base}{random.randint(100,999)}"

        if not User.objects.filter(username=username).exists():

            return username


def generate_username(email):

    base = email.split("@")[0].lower()

    while True:

        username = f"{base}{random.randint(100,999)}"

        if not User.objects.filter(username=username).exists():

            return username