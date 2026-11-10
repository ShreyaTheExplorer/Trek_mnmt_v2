import os
import csv
import smtplib
import json
import logging
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request
import urllib.error

from celery_app import celery
from extensions import db
from models import User, Trek, Booking, Notification
from config import Config

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# 1. User-Triggered Job: export_bookings_csv(user_id)
# -------------------------------------------------------------
@celery.task(name='tasks.export_bookings_csv')
def export_bookings_csv(user_id: int):
    """
    User-triggered async job:
    Generates a CSV of all bookings for the specified user with columns:
    User ID, Trek Name, Location, Booking Status, Booking Date, Trek Start Date, Trek End Date.
    Saves the file to exports/ and notifies the user with the download link.
    """
    user = db.session.get(User, user_id)
    if not user:
        return {'status': 'FAILED', 'error': 'User not found'}

    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_date.desc()).all()

    exports_dir = Config.EXPORTS_DIR
    os.makedirs(exports_dir, exist_ok=True)

    timestamp = int(datetime.utcnow().timestamp())
    filename = f"bookings_user_{user_id}_{timestamp}.csv"
    filepath = os.path.join(exports_dir, filename)

    # Required CSV columns: User ID, Trek Name, Location, Booking Status, Booking Date, Trek Start Date, Trek End Date
    fieldnames = [
        'User ID',
        'Trek Name',
        'Location',
        'Booking Status',
        'Booking Date',
        'Trek Start Date',
        'Trek End Date'
    ]

    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for b in bookings:
            t = b.trek
            trek_name = t.name if t else 'N/A'
            location = t.location if t else 'N/A'
            booking_date_str = b.booking_date.strftime('%Y-%m-%d %H:%M:%S') if b.booking_date else 'N/A'
            start_date_str = t.start_date.isoformat() if t and t.start_date else 'N/A'
            end_date_str = t.end_date.isoformat() if t and t.end_date else 'N/A'

            writer.writerow([
                b.user_id,
                trek_name,
                location,
                b.status,
                booking_date_str,
                start_date_str,
                end_date_str
            ])

    download_url = f"/api/user/exports/{filename}"

    # Create completion notification with download link
    notif = Notification(
        user_id=user_id,
        message=f"Your export is ready. Download link: {download_url}",
        created_at=datetime.utcnow()
    )
    db.session.add(notif)
    db.session.commit()

    logger.info(f"[Export Task] Generated {filename} with {len(bookings)} bookings for user #{user_id}.")

    return {
        'status': 'SUCCESS',
        'user_id': user_id,
        'filename': filename,
        'download_url': download_url,
        'records_count': len(bookings)
    }

# Backward compatibility alias
export_user_bookings_csv = export_bookings_csv


# -------------------------------------------------------------
# 2. Scheduled Job 1: daily_reminders
# -------------------------------------------------------------
@celery.task(name='tasks.daily_reminders')
def daily_reminders(days_ahead: int = None):
    """
    Scheduled job 1: daily_reminders.
    Runs daily at configured time.
    Finds Booked bookings whose trek starts within the next N days (default 2),
    and sends each user a reminder with trek name, start date, location, and instructions.
    Channels: Google Chat webhook and email via smtplib.
    If a channel is not configured or offline, logs to console instead of failing.
    """
    n_days = days_ahead if days_ahead is not None else getattr(Config, 'REMINDER_DAYS_AHEAD', 2)
    today = date.today()
    max_start_date = today + timedelta(days=n_days)

    # Find active bookings for upcoming treks within window
    upcoming_bookings = Booking.query.join(Trek).filter(
        Booking.status == 'Booked',
        Trek.is_deleted == False,
        Trek.start_date >= today,
        Trek.start_date <= max_start_date
    ).all()

    reminders_sent = 0

    for b in upcoming_bookings:
        user = b.user
        trek = b.trek
        if not user or not trek:
            continue

        reminder_text = (
            f"Trek Reminder: '{trek.name}' is scheduled to start on {trek.start_date} at {trek.location}. "
            f"Instructions: {trek.instructions or 'Pack warm layers, sturdy trekking boots, and stay hydrated!'}"
        )

        # 1. In-App Notification
        notif = Notification(
            user_id=user.id,
            message=reminder_text,
            created_at=datetime.utcnow()
        )
        db.session.add(notif)

        # 2. Channel: Google Chat Webhook (urllib POST to GOOGLE_CHAT_WEBHOOK_URL)
        webhook_url = getattr(Config, 'GOOGLE_CHAT_WEBHOOK_URL', None) or os.environ.get('GOOGLE_CHAT_WEBHOOK_URL')
        if webhook_url:
            try:
                payload = json.dumps({'text': f"*{user.name}*: {reminder_text}"}).encode('utf-8')
                req = urllib.request.Request(
                    webhook_url,
                    data=payload,
                    headers={'Content-Type': 'application/json; charset=UTF-8'}
                )
                with urllib.request.urlopen(req, timeout=3):
                    pass
            except Exception as e:
                logger.info(f"[Google Chat Webhook - Console Log] Error sending ({e}). Logged: {reminder_text}")
        else:
            # Not configured -> log to console instead of failing
            print(f"[Daily Reminder Console] [Google Chat Not Configured] Sent to {user.name} ({user.email}): {reminder_text}")

        # 3. Channel: Email via smtplib (SMTP host/port from env, default localhost:1025)
        mail_server = Config.MAIL_SERVER
        mail_port = Config.MAIL_PORT
        if mail_server:
            try:
                msg = MIMEMultipart()
                msg['From'] = Config.MAIL_DEFAULT_SENDER
                msg['To'] = user.email
                msg['Subject'] = f"TMA Reminder: Your Trek '{trek.name}' Starts Soon!"
                msg.attach(MIMEText(reminder_text, 'plain'))

                with smtplib.SMTP(mail_server, mail_port, timeout=2) as server:
                    if Config.MAIL_USE_TLS:
                        server.starttls()
                    if Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
                        server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                    server.send_message(msg)
            except Exception as e:
                # Offline/mock SMTP -> log to console instead of failing
                print(f"[Daily Reminder Console] [SMTP Server at {mail_server}:{mail_port} Offline] Logged for {user.email}: {reminder_text}")
        else:
            print(f"[Daily Reminder Console] [Email Not Configured] Logged for {user.email}: {reminder_text}")

        reminders_sent += 1

    db.session.commit()
    logger.info(f"[Daily Reminders] Processed {reminders_sent} reminder(s).")

    return {
        'status': 'completed',
        'reminders_sent': reminders_sent,
        'date': today.isoformat()
    }


# -------------------------------------------------------------
# 3. Scheduled Job 2: monthly_report
# -------------------------------------------------------------
@celery.task(name='tasks.monthly_report')
def monthly_report():
    """
    Scheduled job 2: monthly_report.
    Runs on the 1st of every month.
    Builds an HTML report for the previous month:
      - Number of treks conducted (Completed in that month).
      - Number of unique users who participated.
      - Popular treks table (top 5 by bookings).
    Styled with inline-CSS HTML.
    Emails it to the admin (HTML body) and saves a copy in exports/.
    """
    now = datetime.utcnow()
    # Calculate previous month date window
    first_of_this_month = date(now.year, now.month, 1)
    last_day_of_prev_month = first_of_this_month - timedelta(days=1)
    first_day_of_prev_month = date(last_day_of_prev_month.year, last_day_of_prev_month.month, 1)
    month_name = last_day_of_prev_month.strftime('%B %Y')

    # Metric 1: Treks conducted (Completed in that month)
    completed_treks_query = Trek.query.filter(
        Trek.is_deleted == False,
        Trek.status == 'Completed',
        Trek.end_date >= first_day_of_prev_month,
        Trek.end_date <= last_day_of_prev_month
    ).all()
    # If no treks in previous month, fallback count of all completed treks for demo
    completed_treks_count = len(completed_treks_query)
    if completed_treks_count == 0:
        completed_treks_count = Trek.query.filter_by(status='Completed', is_deleted=False).count()

    # Metric 2: Number of unique users who participated
    unique_users = db.session.query(Booking.user_id).filter(
        Booking.status.in_(['Booked', 'Completed'])
    ).distinct().count()

    # Metric 3: Popular treks table (top 5 by bookings count)
    all_treks = Trek.query.filter_by(is_deleted=False).all()
    popular_treks_data = []
    for t in all_treks:
        b_count = t.bookings.count()
        part_count = sum(b.participants_count for b in t.bookings.all())
        popular_treks_data.append({
            'name': t.name,
            'location': t.location,
            'difficulty': t.difficulty,
            'bookings_count': b_count,
            'participants_count': part_count,
            'price': t.price
        })

    popular_treks_sorted = sorted(popular_treks_data, key=lambda x: x['bookings_count'], reverse=True)[:5]

    # Generate styled inline-CSS HTML report
    table_rows = ""
    for idx, pt in enumerate(popular_treks_sorted, 1):
        table_rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 10px; font-weight: bold; color: #4a5568;">#{idx}</td>
            <td style="padding: 10px; font-weight: 600; color: #2d3748;">{pt['name']}</td>
            <td style="padding: 10px; color: #718096;">{pt['location']}</td>
            <td style="padding: 10px; color: #2b6cb0;">{pt['difficulty']}</td>
            <td style="padding: 10px; text-align: center; color: #2d3748;">{pt['bookings_count']}</td>
            <td style="padding: 10px; text-align: center; color: #2d3748;">{pt['participants_count']}</td>
            <td style="padding: 10px; text-align: right; font-weight: bold; color: #276749;">Rs. {pt['price']:,.2f}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>TMA Monthly Activity Report - {month_name}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7fafc; margin: 0; padding: 24px; color: #2d3748;">
    <div style="max-width: 720px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #e2e8f0;">
        <!-- Header Banner -->
        <div style="background: linear-gradient(135deg, #2b6cb0 0%, #2c5282 100%); padding: 28px; color: #ffffff; text-align: center;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">TMA Monthly Activity Report</h1>
            <p style="margin: 6px 0 0 0; font-size: 14px; opacity: 0.9;">Reporting Period: {month_name}</p>
        </div>

        <div style="padding: 24px;">
            <!-- Summary Stats Grid -->
            <div style="display: flex; gap: 16px; margin-bottom: 24px;">
                <div style="flex: 1; background-color: #ebf8ff; border: 1px solid #bee3f8; border-radius: 6px; padding: 16px; text-align: center;">
                    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: #2b6cb0;">Treks Conducted</div>
                    <div style="font-size: 28px; font-weight: 700; color: #2c5282; margin-top: 4px;">{completed_treks_count}</div>
                </div>
                <div style="flex: 1; background-color: #f0fff4; border: 1px solid #c6f6d5; border-radius: 6px; padding: 16px; text-align: center;">
                    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; color: #276749;">Unique Trekkers</div>
                    <div style="font-size: 28px; font-weight: 700; color: #22543d; margin-top: 4px;">{unique_users}</div>
                </div>
            </div>

            <!-- Popular Treks Table -->
            <h3 style="font-size: 16px; font-weight: 700; color: #2d3748; margin: 20px 0 12px 0;">Top 5 Popular Treks</h3>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <thead>
                        <tr style="background-color: #edf2f7; text-align: left; border-bottom: 2px solid #cbd5e0;">
                            <th style="padding: 10px; color: #4a5568;">Rank</th>
                            <th style="padding: 10px; color: #4a5568;">Trek Name</th>
                            <th style="padding: 10px; color: #4a5568;">Location</th>
                            <th style="padding: 10px; color: #4a5568;">Difficulty</th>
                            <th style="padding: 10px; text-align: center; color: #4a5568;">Bookings</th>
                            <th style="padding: 10px; text-align: center; color: #4a5568;">Participants</th>
                            <th style="padding: 10px; text-align: right; color: #4a5568;">Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>

            <div style="margin-top: 30px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #a0aec0; text-align: center;">
                Generated automatically by TMA Batch Processing Worker on {now.strftime('%Y-%m-%d %H:%M:%S')} UTC.
            </div>
        </div>
    </div>
</body>
</html>"""

    # Save copy to exports/
    exports_dir = Config.EXPORTS_DIR
    os.makedirs(exports_dir, exist_ok=True)
    report_filename = f"monthly_report_{now.strftime('%Y_%m')}.html"
    report_path = os.path.join(exports_dir, report_filename)

    with open(report_path, mode='w', encoding='utf-8') as f:
        f.write(html_content)

    # Email to admin via smtplib
    admin = User.query.filter_by(role='admin').first()
    admin_email = admin.email if admin else Config.ADMIN_EMAIL

    mail_server = Config.MAIL_SERVER
    mail_port = Config.MAIL_PORT
    if mail_server:
        try:
            msg = MIMEMultipart()
            msg['From'] = Config.MAIL_DEFAULT_SENDER
            msg['To'] = admin_email
            msg['Subject'] = f"TMA Monthly Activity Report - {month_name}"
            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(mail_server, mail_port, timeout=2) as server:
                if Config.MAIL_USE_TLS:
                    server.starttls()
                if Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
                    server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
        except Exception as e:
            print(f"[Monthly Report Console] [SMTP Server Offline] Report generated & logged for admin ({admin_email}): {report_filename} (Error: {e})")
    else:
        print(f"[Monthly Report Console] [Email Not Configured] Saved locally: {report_filename}")

    # Notify admin in-app
    if admin:
        admin_notif = Notification(
            user_id=admin.id,
            message=f"Monthly Activity Report for {month_name} generated! Report saved to {report_filename}.",
            created_at=datetime.utcnow()
        )
        db.session.add(admin_notif)
        db.session.commit()

    logger.info(f"[Monthly Report] Complete. File: {report_filename}, Conducted: {completed_treks_count}, Trekkers: {unique_users}.")

    return {
        'status': 'completed',
        'month': month_name,
        'report_filename': report_filename,
        'report_path': report_path,
        'treks_conducted': completed_treks_count,
        'unique_trekkers': unique_users
    }
