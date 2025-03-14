# SportsApp
Sports App Project

The Sports Score App is a desktop application that fetches sports scores from the ESPN API and displays them in a user-friendly GUI. You can select your league, pick a date, filter games by status (live, scheduled, final), and even dive into detailed box scores for individual games.

Features
Wide League Support: Fetch scores from a variety of leagues, including NFL, NBA, MLB, NHL, MLS, Premier League, La Liga, Bundesliga, Serie A, Ligue 1, UEFA Champions League, UEFA Europa League, NCAA Football, and NCAA Men's Basketball.

Date Selection: View scores for any date—past, present, or future (well, scheduled games, at least!).

Game Filtering: Filter games by status—see all games, or just live, scheduled, or final ones.

Detailed Box Scores: Dive into team and player stats for any game, displayed in a neat tabbed interface.

Sortable Results: Sort the game table by any column (e.g., team names, scores, status) with a click.

Error Handling: Graceful handling of network errors, invalid dates, and unsupported leagues, with helpful error messages.

Logging: Keeps a log of API calls and errors in score_fetcher.log for debugging.

Installation

Prerequisites
Python 3.6+

pip: Comes with Python, ensure it's up to date by running 
- pip install --upgrade pip.

Steps
Clone the Repository
Grab the code from GitHub:

bash
git clone https://github.com/your-username/sports-score-app.git
cd sports-score-app

Install Dependencies

bash
pip install requests pytz

Run the App

bash
python scores_app.py

Usage
Once the app is running, here's how to use it:
Select a League
Use the "Select League" dropdown to pick your favorite league (e.g., NFL, NBA, Premier League).

Choose a Date
Enter a date in YYYY-MM-DD format in the "Select Date" field to view scores for that day.

Filter Games
Use the "Filter" dropdown to show only "Live," "Scheduled," "Final," or "All" games.

Fetch Scores
Click the "Fetch Scores" button to grab the latest scores. The results will appear in a sortable table below.

View Box Scores
Select a game from the "Select Game" dropdown and click "View Box Score" to see detailed stats.

License
This project is licensed under the MIT License. Feel free to use, modify, and distribute it as you see fit—just give credit where credit is due!

