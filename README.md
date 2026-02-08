# Household Chore Chart

A web application for managing household chores, tracking points, and visualizing productivity. Built with Python and Flask.

## Features

*   **Chore Management**: Add, edit, delete, and list chores with point values.
*   **User Profiles**: Manage users, track their total points, and upload profile pictures.
*   **Chore Completion & Logging**: Users can complete chores to earn points, which are logged for history.
*   **Statistics & Charts**: Visualize points distribution and activity over time.
*   **Calendar Integration**: Send chore reminders via email with Google Calendar (.ics) invites.
*   **Mobile Friendly**: Responsive design for use on phones and tablets.

## Getting Started

### Prerequisites

*   Python 3.x installed
*   pip (Python package manager)

### Installation

1.  **Clone the repository** (or download the source code).
2.  **Navigate to the project directory**.
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables**:
    *   Create a `.env` file (you can copy `.env.example` if available, or use the default settings in `app.py`).
    *   Configure `SECRET_KEY`, `DATABASE_URL`, and Email settings if you plan to use the calendar invite feature.
5.  **Initialize the Database**:
    ```bash
    python create_tables.py
    ```
    *   *Optional*: Seed initial data (users/chores) using `python seed_chores.py` or `python seed_admin.py`.

## Running the Application

### Option 1: Using the Batch Script (Windows)

Simply double-click `run_server.bat`. This script will:
*   Display your local IP address (for accessing the app from other devices on your Wi-Fi).
*   Start the server.

### Option 2: Manual Start

Run the following command in your terminal:

```bash
python app.py
```

Access the application at: `http://localhost:5000`

## Technologies Used

*   **Backend**: Python, Flask, SQLAlchemy
*   **Frontend**: HTML, CSS, JavaScript
*   **Database**: SQLite (default)
*   **Other**: `flask-login` for authentication, `flasgger` for API docs, `ics` for creating calendar files.

## Homework 3 Notes

I integrated APIs in a few ways here, firstly, this website is a simple CRUD application which allows users to create, read, update, assign themselves, and delete chores. You can see the API documentation at http://{web_url}:5000/apidocs/. I added weather data into this to inform the user on when the best time to schedule an outdoor chore would be. I used the [National Weather Service](https://api.weather.gov/) API to get this data. I also added a calendar invite feature, which allows the user to send themselves a calendar invite for a chore. This does not technically use an API, but it uses smtplib to send an email with the calendar invite attached. This can use any SMTP server, but I used Brevo.
### 