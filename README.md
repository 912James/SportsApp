# Sports Score Tracker

A desktop app that fetches live sports scores and box scores from the ESPN API, built with Python and a Tkinter GUI. Select a league, pick a date, filter games, and dive into detailed stats—all in one sleek interface.


## Features
- Wide League Support: Covers 14 leagues—NFL, NBA, MLB, NHL, MLS, Premier League, La Liga, Bundesliga, Serie A, Ligue 1, UEFA Champions/Europa Leagues, NCAA Football, and Men’s Basketball.
- Date Flexibility: Fetch scores for any date-past games, today’s action, or scheduled matchups.
- Game Filtering: View all games or filter by status (Live, Scheduled, Final).
- Box Scores: Detailed team and player stats in a tabbed, scrollable UI.
- Sortable Table: Click headers to sort by team, score, status, etc.
- Robust Design: Handles network errors, invalid inputs, and logs activity to score_fetcher.log.

## Tech Stack
- Languages: Python
- Libraries: requests (API calls), pytz (timezones), tkinter (GUI), json (parsing)
- Tools: ESPN API, logging for debugging


## Installation
### Prerequisites
- Python 3.6+
- pip (updated: pip install --upgrade pip)


### Steps
1. Clone the Repo  
   bash    git clone https://github.com/912James/SportsApp.git    cd SportsApp    
2. Install Dependencies  
   bash    pip install requests pytz    
3. Run It  
   bash    python score_app.py    


## Usage
1. Pick a League: Choose from the dropdown (e.g., NBA, Premier League).
2. Set a Date: Enter YYYY-MM-DD (defaults to today, Eastern Time).
3. Filter Games: Select “All,” “Live,” “Scheduled,” or “Final.”
4. Fetch Scores: Hit “Fetch Scores” to populate the table.
5. View Box Scores: Pick a game, click “View Box Score” for stats.


## Why It’s Cool
Built to scratch my sports itch, this app pulls real-time data from ESPN, processes it with Python, and delivers a clean GUI experience. It’s a practical showcase of API integration, data parsing, and user-focused design—skills.
