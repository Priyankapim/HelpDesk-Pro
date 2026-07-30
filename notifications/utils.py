import re

from notifications.email_service import send_email


_KV_PATTERN = re.compile(r'^([A-Za-z][A-Za-z0-9 /]{1,30}):\s*(.+)$')


def _format_message_html(message):
    """
    Takes the plain multi-line text used across the project for
    send_ticket_email(...) and turns it into a nicely styled HTML body:
    - "Label: value" lines become a clean details table
    - lines containing a link get auto-linked
    - everything else becomes a paragraph
    """

    lines = [line.strip() for line in message.strip().splitlines()]
    lines = [line for line in lines if line != ""]

    html_parts = []
    table_rows = []

    def flush_table():
        nonlocal table_rows
        if table_rows:
            rows_html = "".join(
                f'<tr>'
                f'<td style="padding:6px 10px;color:#64748b;font-weight:600;width:160px;">{k}</td>'
                f'<td style="padding:6px 10px;color:#111827;">{v}</td>'
                f'</tr>'
                for k, v in table_rows
            )
            html_parts.append(
                '<table style="width:100%;background:#f8fafc;border-radius:8px;'
                f'margin:16px 0;border-collapse:collapse;">{rows_html}</table>'
            )
            table_rows = []

    for line in lines:

        if "http://" in line or "https://" in line:
            flush_table()
            linked = re.sub(
                r'(https?://\S+)',
                r'<a href="\1" style="color:#2563eb;">\1</a>',
                line
            )
            html_parts.append(f'<p style="margin:10px 0;">{linked}</p>')
            continue

        match = _KV_PATTERN.match(line)

        if match:
            table_rows.append((match.group(1).strip(), match.group(2).strip()))
        else:
            flush_table()
            html_parts.append(f'<p style="margin:10px 0;">{line}</p>')

    flush_table()

    return "".join(html_parts)


def send_ticket_email(subject, message, recipient):

    body_html = _format_message_html(message)

    html_content = f"""
    <html>

    <body style="font-family: Arial, Helvetica, sans-serif;
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

                    <h2 style="color:#2563eb;margin-bottom:8px;">
                        ServiceDesk Pro
                    </h2>

                    {body_html}

                    <p style="margin-top:24px;color:#94a3b8;font-size:13px;">
                        ServiceDesk Pro Team
                    </p>

                </td>
            </tr>

        </table>

    </body>

    </html>
    """

    send_email(
        to_email=recipient,
        subject=subject,
        html_content=html_content,
    )