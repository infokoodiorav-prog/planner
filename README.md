# Field Task Management App

A simple **task management system** for companies where admins assign daily tasks to workers, and workers confirm completed tasks at the end of the day. Ideal for field work like maintenance, cleaning, or deliveries.

---

## Features

- Admin creates users (workers) with email and password
- Workers receive daily tasks linked to specific dates
- Tasks have: description, location, and contact
- Workers mark tasks as **Done** or **Not Done**
- Dashboard shows **progress bar** (tasks done / total)

---

## Future Improvements

- **Reason required** if task is not completed
- Daily task confirmation locks the day
- CSV export for admin reports
- Mobile push notifications
- Google Maps integration for task addresses
- File attachments for tasks
- Dark mode for UI

---

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite (or other, configured in `.env`)
- **Authentication:** Flask-Login
- **Email notifications:** Flask-Mail
- **Rate limiting:** Flask-Limiter
- **Environment variables:** python-dotenv

---

### Workflow

1. **Admin registers or logs in**
2. **Admin creates a worker** with email and password
3. **Admin adds a daily task** with description, location, contact, and date
4. **Worker logs in** via email
5. **Worker sees today's tasks** on the dashboard
6. **Worker marks tasks as Done/Not Done** (reason required if Not Done)
7. **Worker confirms the day** (locks tasks)
8. **Admin exports CSV report** for review

---

## Setup

---

# Clone the repository

git clone https://github.com/infokoodiorav-prog/planner.git
cd task-manager-app

# Install dependencies

pip install -r requirements.txt

# Copy example environment file

cp .env.example .env

# Update .env with your own credentials

SECRET_KEY=your_secret_key
MAIL_USERNAME=youremail@example.com
MAIL_PASSWORD=yourpassword
DATABASE_URL=sqlite:///app.db

# Run the app

python app.py

# Open in browser

http://127.0.0.1:8000
