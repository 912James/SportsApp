import requests
from datetime import datetime
import pytz
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import json

class ScoreFetcher:
    def __init__(self):
        # Set up logging to keep track of what's going on
        logging.basicConfig(filename='score_fetcher.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Base URLs for ESPN
        self.espn_base_url = "https://www.espn.com"
        self.api_base_url = "https://site.api.espn.com/apis/site/v2/sports"
        
        # List of leagues mapped to their specific fetch methods
        self.supported_leagues = {
            "nfl": self.get_nfl_scores,
            "nba": self.get_nba_scores,
            "mlb": self.get_mlb_scores,
            "nhl": self.get_nhl_scores,
            "mls": self.get_mls_scores,
            "premier-league": self.get_premier_league_scores,
            "la-liga": self.get_la_liga_scores,
            "bundesliga": self.get_bundesliga_scores,
            "serie-a": self.get_serie_a_scores,
            "ligue-1": self.get_ligue_1_scores,
            "uefa-champions": self.get_uefa_champions_scores,
            "uefa-europa": self.get_uefa_europa_scores,
            "ncaa-football": self.get_ncaa_football_scores,
            "ncaa-mens-basketball": self.get_ncaa_mens_basketball_scores,
        }
        
        # Mapping of league names to their API paths
        self.league_paths = {
            "nfl": "football/nfl",
            "nba": "basketball/nba",
            "mlb": "baseball/mlb",
            "nhl": "hockey/nhl",
            "mls": "soccer/usa.1",
            "premier-league": "soccer/eng.1",
            "la-liga": "soccer/esp.1",
            "bundesliga": "soccer/ger.1",
            "serie-a": "soccer/ita.1",
            "ligue-1": "soccer/fra.1",
            "uefa-champions": "soccer/uefa.champions",
            "uefa-europa": "soccer/uefa.europa",
            "ncaa-football": "football/college-football",
            "ncaa-mens-basketball": "basketball/mens-college-basketball",
        }

        # Headers to trick the API into thinking we're a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
        }

    # Fetches scores for a given league
    def get_scores(self, league, date_str=None):
        # Make sure the league name is lowercase to avoid case issues
        league = league.lower()
        
        # Check if the league is supported
        if league not in self.supported_leagues:
            return "league_not_supported"

        try:
            # If a date is provided, parse it; otherwise, use today's date in Eastern Time
            if date_str:
                date_obj = datetime.strptime(date_str, "%Y%m%d")
            else:
                date_obj = datetime.now(pytz.timezone('America/New_York'))
                date_str = date_obj.strftime("%Y%m%d")

            # Call the appropriate league-specific method
            return self.supported_leagues[league](date_str)
        
        # If the date format is wrong return a ValueError
        except ValueError:
            return "invalid_date_format"
        
        # If the network has an error return an exception
        except requests.exceptions.RequestException as e:
            return "network_error", str(e)
        
        # If any unexpected errors occur return Exception
        except Exception as e:
            return "unexpected_error", str(e)

    # The API fetching - this method gets the game data
    def _espn_api_fetch(self, league_url_part, date_str):
        # Build the API URL
        api_url = f"{self.api_base_url}/{league_url_part}/scoreboard?dates={date_str}"
        games = []  # Store all the game data in a list

        
        logging.info(f"Fetching scores for {league_url_part} on {date_str} from {api_url}")

        try:
            # Make the API call
            response = requests.get(api_url, headers=self.headers)
            response.raise_for_status()  # If the request fails, throw an exception
            data = response.json()

            # The list of events (games) from the response
            events = data.get('events', [])
            if not events:
                logging.info("No games found for this date - bummer!")
                return []

            # Loop through each game and extract
            for event in events:
                try:
                    game = {}  # Each game gets its a dictionary 
                    game['game_id'] = event['id']
                    game['date'] = datetime.strptime(event['date'], "%Y-%m-%dT%H:%MZ").strftime("%Y-%m-%d")
                    
                    # Convert the UTC time to Eastern Time( Boston ) my current location
                    time_str = event.get('date')
                    try:
                        utc_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%MZ").replace(tzinfo=pytz.UTC)
                        et_time = utc_time.astimezone(pytz.timezone('America/New_York'))
                        game['time'] = et_time.strftime("%I:%M %p ET")
                    except ValueError:
                        game['time'] = ""  # If the time parsing fails, leave it blank

                    game['status'] = event['status']['type']['shortDetail']

                    # ensures there is competition data
                    competitions = event.get('competitions', [])
                    if not competitions:
                        continue

                    competition = competitions[0]
                    competitors = competition.get('competitors', [])
                    if len(competitors) != 2: 
                        continue

                    # Find the home and away teams - using next()
                    home_team = next((team for team in competitors if team['homeAway'] == 'home'), None)
                    away_team = next((team for team in competitors if team['homeAway'] == 'away'), None)

                    if home_team and away_team:
                        game['home_team'] = home_team['team']['displayName']
                        game['away_team'] = away_team['team']['displayName']
                        game['home_score'] = home_team.get('score', 'N/A')  # Use N/A if score is missing
                        game['away_score'] = away_team.get('score', 'N/A')  # Use N/A if score is missing

                        # Simplify the status - Final, Scheduled, or Live
                        if game['status'] == "Final":
                            game['status'] = "Final"
                        elif " - " in game['status']:
                            game['status'] = "Scheduled"
                        else:
                            game['status'] = "Live"

                    games.append(game)

                # Error message if something went wrong while parsing a game
                except (KeyError, ValueError, TypeError) as e:
                    logging.error(f"Error processing game {event.get('id', 'unknown')}: {e}. Skipping!")
                    continue

        # Network error message
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            return []

        return games
    
    # Method to fetch the box score for a specific game
    def get_game_box_score(self, league_url_part, game_id):
        # Build the URL for the box score API
        api_url = f"{self.api_base_url}/{league_url_part}/summary?event={game_id}"
        logging.info(f"Fetching box score for game {game_id} from {api_url}")

        try:
            
            response = requests.get(api_url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Set up a dictionary to hold all the box score information
            box_score = {
                'teams': [],  # Team info
                'team_stats': {},  # Team stats - this provides an overall box score on the performance of the team
                'player_stats': {}  # Player stats - this provides the box score of how an individual performed
            }
            
            # Extract team info - who played, their scores, and if they were home or away
            for team in data.get('header', {}).get('competitions', [{}])[0].get('competitors', []):
                team_info = {
                    'name': team['team']['displayName'],
                    'score': team.get('score', 'N/A'),
                    'homeAway': team['homeAway']
                }
                box_score['teams'].append(team_info)
            
            # Get the team stats
            for team in data.get('boxscore', {}).get('teams', []):
                team_name = team['team']['displayName']
                box_score['team_stats'][team_name] = team.get('statistics', [])

            # Get the player stats
            players_data = data.get('boxscore', {}).get('players', [])
            if not players_data:
                logging.warning("No player stats available - that's a bummer!")
            for team in players_data:
                team_name = team['team']['displayName']
                stats = team.get('statistics', [])
                logging.info(f"Player stats structure for {team_name}: {json.dumps(stats, indent=2)}")
                box_score['player_stats'][team_name] = stats

            return box_score

        # Return an error message if network errors
        except requests.exceptions.RequestException as e:
            logging.error(f"API request for box score failed: {e}")
            return "network_error", str(e)
        
        # Return an error if something unexpected happened
        except Exception as e:
            logging.error(f"Error processing box score: {e}")
            return "unexpected_error", str(e)

    # League specific methods
    # TODO: Refactor to use league_paths dict
    def get_nfl_scores(self, date_str):
        return self._espn_api_fetch("football/nfl", date_str)

    def get_nba_scores(self, date_str):
        return self._espn_api_fetch("basketball/nba", date_str)

    def get_mlb_scores(self, date_str):
        return self._espn_api_fetch("baseball/mlb", date_str)

    def get_nhl_scores(self, date_str):
        return self._espn_api_fetch("hockey/nhl", date_str)

    def get_mls_scores(self, date_str):
        return self._espn_api_fetch("soccer/usa.1", date_str)

    def get_premier_league_scores(self, date_str):
        return self._espn_api_fetch("soccer/eng.1", date_str)

    def get_la_liga_scores(self, date_str):
        return self._espn_api_fetch("soccer/esp.1", date_str)

    def get_bundesliga_scores(self, date_str):
        return self._espn_api_fetch("soccer/ger.1", date_str)

    def get_serie_a_scores(self, date_str):
        return self._espn_api_fetch("soccer/ita.1", date_str)

    def get_ligue_1_scores(self, date_str):
        return self._espn_api_fetch("soccer/fra.1", date_str)

    def get_uefa_champions_scores(self, date_str):
        return self._espn_api_fetch("soccer/uefa.champions", date_str)

    def get_uefa_europa_scores(self, date_str):
        return self._espn_api_fetch("soccer/uefa.europa", date_str)

    def get_ncaa_football_scores(self, date_str):
        return self._espn_api_fetch("football/college-football", date_str)

    def get_ncaa_mens_basketball_scores(self, date_str):
        return self._espn_api_fetch("basketball/mens-college-basketball", date_str)

# GUI - allows for the user to interact with the app
class ScoreApp:
    def __init__(self, master):
        self.master = master
        master.title("Sports Score App")
        master.geometry("900x700")
        master.configure(bg="#f0f0f0")  # Light gray background

        # ScoreFetcher backend instance 
        self.fetcher = ScoreFetcher()

        # GUI styling
        style = ttk.Style()
        style.theme_use('clam') 
        style.configure("TLabel", font=("Helvetica", 12), background="#f0f0f0")
        style.configure("TButton", font=("Helvetica", 12), padding=6, background="#4CAF50", foreground="white")
        style.map("TButton", background=[('active', '#45a049')])
        style.configure("TCombobox", font=("Helvetica", 12))
        style.configure("Treeview", font=("Helvetica", 11), rowheight=25)
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))

        # Builds the UI
        self.create_widgets()

    # Method that sets up the widgets in the GUI
    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # League selection frame
        league_frame = ttk.LabelFrame(main_frame, text="League Selection", padding="10")
        league_frame.pack(fill=tk.X, pady=5)

        self.league_label = ttk.Label(league_frame, text="Select League:")
        self.league_label.pack(side=tk.LEFT, padx=5)

        self.league_var = tk.StringVar()
        self.league_combo = ttk.Combobox(league_frame, textvariable=self.league_var,
                                         values=list(self.fetcher.supported_leagues.keys()))
        self.league_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.league_combo.set("nba")  # Default to NBA - Lets Go CELTICS!!!!!

        # Date selection frame
        date_frame = ttk.LabelFrame(main_frame, text="Date Selection", padding="10")
        date_frame.pack(fill=tk.X, pady=5)

        self.date_label = ttk.Label(date_frame, text="Select Date (YYYY-MM-DD):")
        self.date_label.pack(side=tk.LEFT, padx=5)

        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=12)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        boston_tz = pytz.timezone('America/New_York')
        self.date_var.set(datetime.now(boston_tz).strftime("%Y-%m-%d"))  # Default to today in Eastern time zone

        # Filter frame
        filter_frame = ttk.LabelFrame(main_frame, text="Filter Options", padding="10")
        filter_frame.pack(fill=tk.X, pady=5)

        self.filter_label = ttk.Label(filter_frame, text="Filter:")
        self.filter_label.pack(side=tk.LEFT, padx=5)

        self.filter_var = tk.StringVar()
        self.filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                         values=["All", "Live", "Scheduled", "Final"])
        self.filter_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.filter_combo.set("All")  # Show all games

        # Game selection frame
        game_frame = ttk.LabelFrame(main_frame, text="Game Selection", padding="10")
        game_frame.pack(fill=tk.X, pady=5)

        self.game_label = ttk.Label(game_frame, text="Select Game:")
        self.game_label.pack(side=tk.LEFT, padx=5)

        self.game_var = tk.StringVar()
        self.game_combo = ttk.Combobox(game_frame, textvariable=self.game_var, state="readonly")
        self.game_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.box_score_button = ttk.Button(game_frame, text="View Box Score", command=self.view_box_score)
        self.box_score_button.pack(side=tk.LEFT, padx=5)

        # "Fetch Scores" and "Refresh Scores" buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.fetch_button = ttk.Button(button_frame, text="Fetch Scores", command=self.fetch_and_display)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        self.refresh_button = ttk.Button(button_frame, text="Refresh Scores", command=self.fetch_and_display)
        self.refresh_button.pack(side=tk.LEFT, padx=5)  # Refresh scores

        # Results frame - Display table of games
        results_frame = ttk.LabelFrame(main_frame, text="Game Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ("away_team", "home_team", "away_score", "home_score", "status", "date", "time")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Sortable table header
        for col in columns:
            self.results_tree.heading(col, text=col.replace("_", " ").title(),
                                      command=lambda c=col: self.sort_treeview(c, False))
            self.results_tree.column(col, width=100, anchor="center")

        # Scrollbar if list becomes long
        self.scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=self.scrollbar.set)

    # Method to sort the table
    def sort_treeview(self, col, reverse):
        data = [(self.results_tree.set(child, col), child) for child in self.results_tree.get_children('')]
        data.sort(reverse=reverse)
        for index, (val, child) in enumerate(data):
            self.results_tree.move(child, '', index)
        self.results_tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    # Fetch scores and displays them in the table
    def fetch_and_display(self):
        league = self.league_var.get()
        date_str = self.date_var.get()
        try:
            # Parse the date
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_str_api = date_obj.strftime("%Y%m%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        filter_option = self.filter_var.get()

        # Fetch the scores
        result = self.fetcher.get_scores(league, date_str_api)

        # Clear out the old table data
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        self.game_combo['values'] = []  # Clear the game
        self.game_var.set("")

        # Check to see if we have a list of games
        if isinstance(result, list):
            if result:
                # Apply the filter if it's not "All"
                filtered_games = result
                if filter_option != "All":
                    filtered_games = [game for game in result if game['status'] == filter_option]

                if filtered_games:
                    game_options = []
                    # Populate the table and game dropdown with the filtered games
                    for game in filtered_games:
                        game_str = f"{game['away_team']} @ {game['home_team']} ({game['date']} {game['time']})"
                        game_options.append((game_str, game['game_id']))
                        self.results_tree.insert("", "end", values=(
                            game['away_team'],
                            game['home_team'],
                            game['away_score'],
                            game['home_score'],
                            game['status'],
                            game['date'],
                            game['time']
                        ))
                    self.game_combo['values'] = [option[0] for option in game_options]
                    self.game_combo.game_ids = {option[0]: option[1] for option in game_options}
                else:
                    messagebox.showinfo("Info", f"No {filter_option.lower()} games found for the selected league and date.")
            else:
                messagebox.showinfo("Info", "No games found for the selected league and date.")
        else:
            # Error messsages for user errors
            if result == "league_not_supported":
                messagebox.showerror("Error", "Selected league is not supported.")
            elif result == "invalid_date_format":
                messagebox.showerror("Error", "Invalid date format. Please use YYYYMMDD.")
            elif result[0] == "network_error":
                messagebox.showerror("Network Error", f"Failed to connect: {result[1]}")
            elif result[0] == "unexpected_error":
                messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {result[1]}")

    # Method that shows the box score in a new window
    def view_box_score(self):
        selected_game = self.game_var.get()
        if not selected_game:
            messagebox.showwarning("Warning", "Please select a game to view the box score.")
            return

        game_id = self.game_combo.game_ids.get(selected_game)
        if not game_id:
            messagebox.showerror("Error", "Invalid game selection.")
            return

        league = self.league_var.get()
        league_url_part = self.fetcher.league_paths.get(league)
        if not league_url_part:
            messagebox.showerror("Error", "Unable to determine league URL part.")
            return

        # Fetch the box score
        box_score = self.fetcher.get_game_box_score(league_url_part, game_id)
        if isinstance(box_score, tuple):
            if box_score[0] == "network_error":
                messagebox.showerror("Network Error", f"Failed to fetch box score: {box_score[1]}")
            elif box_score[0] == "unexpected_error":
                messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {box_score[1]}")
            return

        # Create a new window for the box score
        box_score_window = tk.Toplevel(self.master)
        box_score_window.title(f"Box Score - {selected_game}")
        box_score_window.geometry("1200x800")
        box_score_window.configure(bg="#f0f0f0")

        box_score_frame = ttk.Frame(box_score_window, padding="10")
        box_score_frame.pack(fill=tk.BOTH, expand=True)

        # Show the teams and their scores
        team_frame = ttk.LabelFrame(box_score_frame, text="Teams", padding="10")
        team_frame.pack(fill=tk.X, pady=5)
        for team in box_score['teams']:
            team_label = ttk.Label(team_frame, text=f"{team['name']} ({team['homeAway']}): {team['score']}")
            team_label.pack(anchor="w")

        # Team stats
        team_stats_frame = ttk.LabelFrame(box_score_frame, text="Team Statistics", padding="10")
        team_stats_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        team_stats_notebook = ttk.Notebook(team_stats_frame)
        team_stats_notebook.pack(fill=tk.BOTH, expand=True)

        for team_name, stats in box_score['team_stats'].items():
            team_tab = ttk.Frame(team_stats_notebook)
            team_stats_notebook.add(team_tab, text=team_name)
            
            stats_container = ttk.Frame(team_tab)
            stats_container.pack(fill=tk.BOTH, expand=True)
            
            # Use a Treeview to display stats
            stats_tree = ttk.Treeview(stats_container, columns=("stat", "value"), show="headings")
            stats_tree.heading("stat", text="Statistic")
            stats_tree.heading("value", text="Value")
            stats_tree.column("stat", width=200, anchor="w")  
            stats_tree.column("value", width=150, anchor="center")
            
            # Add scrollbars in case of a lot of stats
            v_scrollbar = ttk.Scrollbar(stats_container, orient="vertical", command=stats_tree.yview)
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            stats_tree.configure(yscrollcommand=v_scrollbar.set)
            
            h_scrollbar = ttk.Scrollbar(stats_container, orient="horizontal", command=stats_tree.xview)
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            stats_tree.configure(xscrollcommand=h_scrollbar.set)
            
            stats_tree.pack(fill=tk.BOTH, expand=True)
            for stat in stats:
                stats_tree.insert("", "end", values=(stat['name'], stat['displayValue']))

        # Player stats
        player_stats_frame = ttk.LabelFrame(box_score_frame, text="Player Statistics", padding="10")
        player_stats_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        player_stats_notebook = ttk.Notebook(player_stats_frame)
        player_stats_notebook.pack(fill=tk.BOTH, expand=True)

        for team_name, stat_categories in box_score['player_stats'].items():
            if not stat_categories:
                player_stats_notebook.add(ttk.Label(player_stats_notebook, text="No player stats available"), text=team_name)
                continue

            # Player stats are grouped by category
            for stat_category in stat_categories:
                category_name = stat_category.get('name', 'General')
                team_tab = ttk.Frame(player_stats_notebook)
                player_stats_notebook.add(team_tab, text=f"{team_name} - {category_name}")

                athletes = stat_category.get('athletes', [])
                if not athletes:
                    ttk.Label(team_tab, text="No player stats available for this category").pack()
                    continue

                first_athlete = athletes[0]
                stats_list = first_athlete.get('stats', [])
                
                if not stats_list:
                    ttk.Label(team_tab, text="No detailed stats available").pack()
                    continue
                
                stats_container = ttk.Frame(team_tab)
                stats_container.pack(fill=tk.BOTH, expand=True)
                
                # Player stats to check if the stats are dictionaries, or lists
                if isinstance(stats_list[0], dict):
                    columns = ("player",) + tuple(stat.get('name', 'Unknown') for stat in stats_list)
                    stats_tree = ttk.Treeview(stats_container, columns=columns, show="headings")
                    stats_tree.heading("player", text="Player")
                    stats_tree.column("player", width=200, anchor="w")
                    for stat in stats_list:
                        stat_name = stat.get('name', 'Unknown')
                        stats_tree.heading(stat_name, text=stat_name)
                        stats_tree.column(stat_name, width=100, anchor="center")
                else:
                    columns = ("player",) + tuple(f"Stat_{i+1}" for i in range(len(stats_list)))
                    stats_tree = ttk.Treeview(stats_container, columns=columns, show="headings")
                    stats_tree.heading("player", text="Player")
                    stats_tree.column("player", width=200, anchor="w")
                    for i, col in enumerate(columns[1:], 1):
                        stats_tree.heading(col, text=f"Stat {i}")
                        stats_tree.column(col, width=100, anchor="center")

                # Add scrollbars
                v_scrollbar = ttk.Scrollbar(stats_container, orient="vertical", command=stats_tree.yview)
                v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                stats_tree.configure(yscrollcommand=v_scrollbar.set)
                
                h_scrollbar = ttk.Scrollbar(stats_container, orient="horizontal", command=stats_tree.xview)
                h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
                stats_tree.configure(xscrollcommand=h_scrollbar.set)
                
                stats_tree.pack(fill=tk.BOTH, expand=True)

                # Add each player's stats to the table
                for athlete in athletes:
                    stats = athlete.get('stats', [])
                    if isinstance(stats, list) and stats and isinstance(stats[0], dict):
                        values = (athlete['athlete']['displayName'],) + tuple(stat.get('displayValue', 'N/A') for stat in stats)
                    else:
                        values = (athlete['athlete']['displayName'],) + tuple(stats if stats else ['N/A'] * (len(columns) - 1))
                    stats_tree.insert("", "end", values=values)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScoreApp(root)
    root.mainloop()
