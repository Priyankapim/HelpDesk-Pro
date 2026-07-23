import random
import string
from .models import User
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse

def parse_user_agent(ua_string):
    """
    Lightweight browser/OS label from a raw User-Agent string,
    e.g. "Chrome on Windows". No external dependency required.
    """

    if not ua_string:
        return "Unknown device"

    ua = ua_string

    if "Windows" in ua:
        os_name = "Windows"
    elif "Mac OS" in ua or "Macintosh" in ua:
        os_name = "macOS"
    elif "Android" in ua:
        os_name = "Android"
    elif "iPhone" in ua or "iPad" in ua:
        os_name = "iOS"
    elif "Linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Unknown OS"

    if "Edg/" in ua:
        browser = "Edge"
    elif "OPR/" in ua or "Opera" in ua:
        browser = "Opera"
    elif "Chrome/" in ua:
        browser = "Chrome"
    elif "Firefox/" in ua:
        browser = "Firefox"
    elif "Safari/" in ua:
        browser = "Safari"
    else:
        browser = "Unknown browser"

    return f"{browser} on {os_name}"

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




def send_invitation_email(invitation):

    accept_link = (
        f"http://127.0.0.1:8000"
        f"{reverse('accept_invitation', args=[invitation.token])}"
    )

    subject = "You're Invited to HelpDesk Pro"

    html_content = f"""
    <html>

    <body style="font-family:Arial,Helvetica,sans-serif;
                 font-size:15px;
                 color:#334155;
                 line-height:1.7;
                 background:#f8fafc;
                 padding:30px;">

        <table
            width="600"
            align="center"
            style="
                background:#ffffff;
                border-radius:12px;
                border:1px solid #e2e8f0;
                padding:40px;
            ">

            <tr>

                <td>

                    <h2
                        style="
                            color:#2563eb;
                            margin-bottom:8px;
                        ">

                        HelpDesk Pro

                    </h2>

                    <p>

                        Hello
                        <strong>

                            {invitation.first_name}

                        </strong>,

                    </p>

                    <p>

                        You have been invited to join
                        <strong>

                            HelpDesk Pro

                        </strong>.

                    </p>

                    <table
                        style="
                            width:100%;
                            background:#f8fafc;
                            border-radius:8px;
                            padding:15px;
                            margin:20px 0;
                        ">

                        <tr>

                            <td>

                                <strong>Email</strong>

                            </td>

                            <td>

                                {invitation.email}

                            </td>

                        </tr>

                        <tr>

                            <td>

                                <strong>Role</strong>

                            </td>

                            <td>

                                {invitation.get_role_display()}

                            </td>

                        </tr>

                        <tr>

                            <td>

                                <strong>Department</strong>

                            </td>

                            <td>

                                {invitation.department}

                            </td>

                        </tr>

                    </table>

                    <p>

                        Click the button below to activate your account.

                    </p>

                    <p
                        style="
                            text-align:center;
                            margin:35px 0;
                        ">

                        <a
                            href="{accept_link}"

                            style="
                                background:#2563eb;
                                color:#ffffff;
                                text-decoration:none;
                                padding:14px 30px;
                                border-radius:8px;
                                font-weight:600;
                                display:inline-block;
                            ">

                            Accept Invitation

                        </a>

                    </p>

                    <p>

                        This invitation will expire in
                        <strong>

                            7 days

                        </strong>.

                    </p>

                    <hr>

                    <p
                        style="
                            color:#64748b;
                            font-size:13px;
                        ">

                        If the button doesn't work, copy this link into your browser.

                    </p>

                    <p
                        style="
                            word-break:break-all;
                            color:#2563eb;
                        ">

                        {accept_link}

                    </p>

                    <br>

                    <p>

                        Regards,

                        <br>

                        <strong>

                            HelpDesk Pro Team

                        </strong>

                    </p>

                </td>

            </tr>

        </table>

    </body>

    </html>
    """

    email = EmailMultiAlternatives(

        subject,

        "",

        settings.DEFAULT_FROM_EMAIL,

        [invitation.email]

    )

    email.attach_alternative(
        html_content,
        "text/html"
    )

    email.send()