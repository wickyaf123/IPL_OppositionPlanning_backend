from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import pandas as pd
import json
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from contextlib import asynccontextmanager
from insights import PLAYER_INSIGHTS, TEAM_INSIGHTS, VENUE_INSIGHTS, OVERALL_BOWLING_AVERAGES
from config import settings
import uvicorn
from pydantic import BaseModel
from gemini_ppt_generator import GeminiPPTGenerator
from screenshot_ppt_generator import ScreenshotPPTGenerator
import io

# Global data variables
batting_data = None
team_data = None
batter_vs_bowler_data = None
team_vs_bowler_data = None
venue_data = None
over_by_over_data = None
dismissal_location_data = None
batter_strike_rate_zones_data = None
venue_toss_decisions_data = None
venue_toss_situation_data = None
nba_team_stats_data = None
nba_player_stats_data = None
batter_wagon_wheel_data = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global batting_data, team_data, batter_vs_bowler_data, team_vs_bowler_data, venue_data, over_by_over_data, dismissal_location_data, batter_strike_rate_zones_data, venue_toss_decisions_data, venue_toss_situation_data, nba_team_stats_data, nba_player_stats_data, batter_wagon_wheel_data
    try:
        DATA_DIR = Path(__file__).parent / "data"
        batting_data = pd.read_csv(DATA_DIR / "IPL_21_24_Batting.csv")
        team_data = pd.read_csv(DATA_DIR / "IPL_Team_BattingData_21_24.csv")
        batter_vs_bowler_data = pd.read_csv(DATA_DIR / "Batters_StrikeRateVSBowlerTypeNew.csv")
        team_vs_bowler_data = pd.read_csv(DATA_DIR / "Team_vs_BowlingType.csv")
        venue_data = pd.read_csv(DATA_DIR / "IPL_Venue_details.csv")
        over_by_over_data = pd.read_csv(DATA_DIR / "over_by_over_breakdown2025.csv")
        dismissal_location_data = pd.read_csv(DATA_DIR / "Striker_vs_Where_Caught_Counts.csv")
        batter_strike_rate_zones_data = pd.read_csv(DATA_DIR / "batter_line_length_SR_long.csv")
        venue_toss_decisions_data = pd.read_csv(DATA_DIR / "VenueTossDecisions.csv")
        venue_toss_situation_data = pd.read_csv(DATA_DIR / "VenueToss_Situation_Details.csv")
        nba_team_stats_data = pd.read_csv(DATA_DIR / "NBA_Team_Stats_041125.csv")
        nba_player_stats_data = pd.read_csv(DATA_DIR / "NBA_PlayerStats_041125.csv")
        batter_wagon_wheel_data = pd.read_csv(DATA_DIR / "Batter_WagonWheel.csv")
        print("Data loaded successfully!")
    except Exception as e:
        print(f"Error loading data: {e}")
    
    yield
    
    # Shutdown (cleanup if needed)
    print("Shutting down...")

app = FastAPI(title="IPL Opposition Planning API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Team players mapping
TEAM_PLAYERS = {
    'Chennai Super Kings': [
        'Ruturaj Gaikwad', 'Devon Conway', 'Ravindra Jadeja', 
        'Mahendra Singh Dhoni', 'Shivam Dube', 'Moeen Ali', 'Deepak Chahar', 
        'Dwayne Bravo', 'Tushar Deshpande'
    ],
    'Mumbai Indians': [
        'Ishan Kishan', 'Rohit Sharma', 'Suryakumar Yadav', 'Tilak Varma', 'Tim David',
        'Hardik Pandya',  'Jasprit Bumrah', 
        'Rahul Chahar', 'Tymal Mills', 'Kieron Pollard'
    ],
    'Royal Challengers Bangalore': [
        'Virat Kohli', 'Faf du Plessis', 'Glenn Maxwell', 'Will Jacks',
        'Rajat Patidar', 'Dinesh Karthik', 'Cameron Green', 'Lockie Ferguson',
        'Mohammed Siraj', 'Josh Hazlewood', 'Yash Dayal'
    ],
    'Kolkata Knight Riders': [
        'Venkatesh Iyer', 'Shreyas Iyer', 'Nitish Rana',
        'Andre Russell', 'Rinku Singh', 'Phil Salt', 'Sunil Narine', 
        'Pat Cummins', 'Varun Chakravarthy'
    ],
    'Delhi Capitals': [
        'David Warner', 'Prithvi Shaw', 'Rishabh Pant', 'Axar Patel',
        'Lalit Yadav', 'Rovman Powell', 'Shardul Thakur', 'Kuldeep Yadav',
        'Anrich Nortje', 'Mustafizur Rahman', 'Khaleel Ahmed'
    ],
    'Punjab Kings': [
        'Mayank Agarwal', 'Shikhar Dhawan', 'Liam Livingstone',
        'Jonny Bairstow', 'Shahrukh Khan', 'Sam Curran', 'Kagiso Rabada', 
        'Arshdeep Singh', 'Rahul Chahar'
    ],
    'Rajasthan Royals': [
        'Jos Buttler', 'Yashasvi Jaiswal', 'Sanju Samson', 'Shimron Hetmyer',
        'Riyan Parag', 'Devdutt Padikkal', 'Ravichandran Ashwin', 'Trent Boult',
        'Prasidh Krishna', 'Yuzvendra Chahal', 'Obed McCoy'
    ],
    'Sunrisers Hyderabad': [
        'Kane Williamson', 'Abhishek Sharma','Travis Head' 'Aiden Markram', 'Nicholas Pooran',
        'Abdul Samad',  'Washington Sundar', 'Bhuvneshwar Kumar', 
        'T Natarajan', 'Umran Malik', 'Marco Jansen'
    ],
    'Gujarat Titans': [
        'David Miller', 'Sai Sudharsan',
        'Rahul Tewatia', 'Wriddhiman Saha', 'Rashid Khan', 'Mohammed Shami', 
         'Alzarri Joseph',
    ],
    'Lucknow Super Giants': [
        'KL Rahul', 'Quinton de Kock', 'Marcus Stoinis', 'Deepak Hooda',
        'Ayush Badoni', 'Krunal Pandya', 'Jason Holder', 'Avesh Khan',
        'Dushmantha Chameera', 'Ravi Bishnoi', 'Mohsin Khan'
    ]
}

# Sample venues
VENUES = [
    "M. A. Chidambaram Stadium, Chennai",
    "Wankhede Stadium, Mumbai",
    "M. Chinnaswamy Stadium, Bangalore",
    "Eden Gardens, Kolkata",
    "Arun Jaitley Stadium, Delhi",
    "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "Sawai Mansingh Stadium, Jaipur",
    "Rajiv Gandhi International Stadium, Hyderabad",
    "Narendra Modi Stadium, Ahmedabad",
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow"
]

# Data directory path
DATA_DIR = Path(__file__).parent / "data"

@app.get("/")
async def root():
    return {"message": "IPL Opposition Planning API is running!"}

@app.get("/config")
async def get_config():
    """Get API configuration"""
    return {
        "api_url": settings.api_url,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

@app.get("/teams")
async def get_teams():
    """Get all IPL teams"""
    return {"teams": list(TEAM_PLAYERS.keys())}

@app.get("/teams/{team_name}/players")
async def get_team_players(team_name: str):
    """Get players for a specific team"""
    if team_name not in TEAM_PLAYERS:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"team": team_name, "players": TEAM_PLAYERS[team_name]}

@app.get("/venues")
async def get_venues():
    """Get all venues"""
    return {"venues": VENUES}

@app.get("/player/{player_name}/insights")
async def get_player_insights(player_name: str):
    """Get insights for a specific player"""
    if player_name in PLAYER_INSIGHTS:
        return {
            "player": player_name,
            "insights": PLAYER_INSIGHTS[player_name]
        }
    else:
        # Generate default insights for players not in hardcoded data
        return {
            "player": player_name,
            "insights": {
                "ai_insights": [
                    f"{player_name} shows consistent performance across different match situations",
                    "Demonstrates good adaptability to various bowling attacks",
                    "Maintains steady scoring rate throughout innings"
                ],
                "strengths": [
                    "Solid technique against both pace and spin bowling",
                    "Good strike rotation ability"
                ],
                "areas_for_improvement": [
                    "Can improve boundary hitting percentage",
                    "Needs to work on powerplay acceleration"
                ]
            }
        }

@app.get("/team/{team_name}/insights")
async def get_team_insights(team_name: str):
    """Get insights for a specific team"""
    if team_name in TEAM_INSIGHTS:
        return {
            "team": team_name,
            "insights": TEAM_INSIGHTS[team_name]
        }
    else:
        raise HTTPException(status_code=404, detail="Team insights not found")

@app.get("/venue/{venue_name}/insights")
async def get_venue_insights(venue_name: str):
    """Get insights for a specific venue"""
    if venue_name in VENUE_INSIGHTS:
        return {
            "venue": venue_name,
            "insights": VENUE_INSIGHTS[venue_name]
        }
    else:
        # Generate default venue insights
        return {
            "venue": venue_name,
            "insights": {
                "insights": [
                    f"{venue_name} provides balanced conditions for batting",
                    "Good scoring opportunities in all phases of the game",
                    "Suitable for both pace and spin bowling",
                    "Average scoring rate supports competitive matches",
                    "Boundary hitting opportunities available throughout innings"
                ]
            }
        }

@app.get("/scatter-plot-data")
async def get_scatter_plot_data(selected_players: str = ""):
    """Get scatter plot data for players"""
    if batting_data is None:
        # Return hardcoded data if CSV not loaded
        key_players_data = [
            {'name': 'Shubman Gill', 'first_innings_avg': 45.2, 'second_innings_avg': 38.5, 'first_innings_sr': 142.8, 'second_innings_sr': 135.2},
            {'name': 'Faf du Plessis', 'first_innings_avg': 42.1, 'second_innings_avg': 35.8, 'first_innings_sr': 138.5, 'second_innings_sr': 132.1},
            {'name': 'Ruturaj Gaikwad', 'first_innings_avg': 41.8, 'second_innings_avg': 34.2, 'first_innings_sr': 136.9, 'second_innings_sr': 129.8},
            {'name': 'Virat Kohli', 'first_innings_avg': 48.5, 'second_innings_avg': 42.1, 'first_innings_sr': 140.2, 'second_innings_sr': 134.8},
            {'name': 'KL Rahul', 'first_innings_avg': 44.3, 'second_innings_avg': 39.7, 'first_innings_sr': 139.1, 'second_innings_sr': 133.5},
            {'name': 'Jos Buttler', 'first_innings_avg': 41.5, 'second_innings_avg': 36.8, 'first_innings_sr': 143.6, 'second_innings_sr': 138.2},
            {'name': 'Sanju Samson', 'first_innings_avg': 38.9, 'second_innings_avg': 33.5, 'first_innings_sr': 141.2, 'second_innings_sr': 135.8},
            {'name': 'Shikhar Dhawan', 'first_innings_avg': 39.8, 'second_innings_avg': 35.2, 'first_innings_sr': 134.5, 'second_innings_sr': 128.9},
            {'name': 'Suryakumar Yadav', 'first_innings_avg': 40.2, 'second_innings_avg': 36.1, 'first_innings_sr': 145.8, 'second_innings_sr': 140.2},
            {'name': 'Yashasvi Jaiswal', 'first_innings_avg': 43.1, 'second_innings_avg': 37.8, 'first_innings_sr': 138.9, 'second_innings_sr': 132.5},
            {'name': 'Ishan Kishan', 'first_innings_avg': 37.5, 'second_innings_avg': 32.8, 'first_innings_sr': 142.1, 'second_innings_sr': 136.8},
            {'name': 'Rohit Sharma', 'first_innings_avg': 46.2, 'second_innings_avg': 40.5, 'first_innings_sr': 137.8, 'second_innings_sr': 131.2},
            {'name': 'Shivam Dube', 'first_innings_avg': 35.8, 'second_innings_avg': 31.2, 'first_innings_sr': 144.5, 'second_innings_sr': 138.9},
            {'name': 'Venkatesh Iyer', 'first_innings_avg': 36.9, 'second_innings_avg': 32.1, 'first_innings_sr': 139.8, 'second_innings_sr': 133.5},
            {'name': 'David Warner', 'first_innings_avg': 44.8, 'second_innings_avg': 39.2, 'first_innings_sr': 141.5, 'second_innings_sr': 135.8}
        ]
        
        # Add selected players if not in the list
        selected_player_list = selected_players.split(',') if selected_players else []
        for player in selected_player_list:
            player = player.strip()
            if player and not any(p['name'] == player for p in key_players_data):
                # Add default data for selected players not in the key list
                key_players_data.append({
                    'name': player,
                    'first_innings_avg': 35.0 + (len(player) % 10),  # Some variation based on name
                    'second_innings_avg': 30.0 + (len(player) % 8),
                    'first_innings_sr': 135.0 + (len(player) % 15),
                    'second_innings_sr': 130.0 + (len(player) % 12)
                })
        
        return {"scatter_data": key_players_data}
    
    # Define the 15 key players for scatter plot
    key_players = [
        'Shubman Gill', 'Faf du Plessis', 'Ruturaj Gaikwad', 'Virat Kohli',
        'KL Rahul', 'Jos Buttler', 'Sanju Samson', 'Shikhar Dhawan',
        'Suryakumar Yadav', 'Yashasvi Jaiswal', 'Ishan Kishan', 'Rohit Sharma',
        'Shivam Dube', 'Venkatesh Iyer', 'David Warner'
    ]
    
    # Parse selected players
    selected_player_list = selected_players.split(',') if selected_players else []
    selected_player_list = [p.strip() for p in selected_player_list if p.strip()]
    
    # Combine key players with selected players
    all_players_to_show = list(set(key_players + selected_player_list))
    
    scatter_data = []
    for _, row in batting_data.iterrows():
        if row['Batter_Name'] in all_players_to_show:
            # Convert strike rate strings to float values
            first_sr = row['strike_rate_1st_innings']
            second_sr = row['strike_rate_2nd_innings']
            
            # Remove % symbol and convert to float
            if isinstance(first_sr, str) and first_sr.endswith('%'):
                first_sr = float(first_sr.replace('%', ''))
            if isinstance(second_sr, str) and second_sr.endswith('%'):
                second_sr = float(second_sr.replace('%', ''))
                
            scatter_data.append({
                'name': row['Batter_Name'],
                'first_innings_avg': float(row['batting_average_1st_innings']) if row['batting_average_1st_innings'] else 0,
                'second_innings_avg': float(row['batting_average_2nd_innings']) if row['batting_average_2nd_innings'] else 0,
                'first_innings_sr': float(first_sr) if first_sr else 0,
                'second_innings_sr': float(second_sr) if second_sr else 0,
                'isSelected': row['Batter_Name'] in selected_player_list
            })
    
    # Add any selected players not found in the data with default values
    found_players = [p['name'] for p in scatter_data]
    for player in selected_player_list:
        if player not in found_players:
            scatter_data.append({
                'name': player,
                'first_innings_avg': 35.0 + (len(player) % 10),
                'second_innings_avg': 30.0 + (len(player) % 8),
                'first_innings_sr': 135.0 + (len(player) % 15),
                'second_innings_sr': 130.0 + (len(player) % 12),
                'isSelected': True
            })
    
    return {"scatter_data": scatter_data}

@app.get("/team-scatter-plot-data")
async def get_team_scatter_plot_data():
    """Get scatter plot data for teams"""
    # Hardcoded team data for scatter plot
    team_scatter_data = [
        {"name": "Chennai Super Kings", "first_innings_avg": 173.59, "second_innings_avg": 152.45, "first_innings_sr": 144.27, "second_innings_sr": 134.38},
        {"name": "Mumbai Indians", "first_innings_avg": 170.25, "second_innings_avg": 151.25, "first_innings_sr": 140.05, "second_innings_sr": 138.75},
        {"name": "Royal Challengers Bangalore", "first_innings_avg": 175.85, "second_innings_avg": 146.75, "first_innings_sr": 142.15, "second_innings_sr": 135.25},
        {"name": "Kolkata Knight Riders", "first_innings_avg": 169.44, "second_innings_avg": 149.25, "first_innings_sr": 141.33, "second_innings_sr": 134.38},
        {"name": "Delhi Capitals", "first_innings_avg": 166.58, "second_innings_avg": 151.18, "first_innings_sr": 137.81, "second_innings_sr": 135.23},
        {"name": "Punjab Kings", "first_innings_avg": 168.25, "second_innings_avg": 148.50, "first_innings_sr": 136.75, "second_innings_sr": 134.25},
        {"name": "Rajasthan Royals", "first_innings_avg": 165.25, "second_innings_avg": 159.75, "first_innings_sr": 139.85, "second_innings_sr": 137.25},
        {"name": "Sunrisers Hyderabad", "first_innings_avg": 167.50, "second_innings_avg": 154.25, "first_innings_sr": 139.25, "second_innings_sr": 136.75},
        {"name": "Gujarat Titans", "first_innings_avg": 164.75, "second_innings_avg": 157.75, "first_innings_sr": 138.50, "second_innings_sr": 135.60},
        {"name": "Lucknow Super Giants", "first_innings_avg": 170.17, "second_innings_avg": 150.81, "first_innings_sr": 135.25, "second_innings_sr": 133.75}
    ]
    
    return {"team_scatter_data": team_scatter_data}

@app.get("/player/{player_name}/bowling-stats")
async def get_player_bowling_stats(player_name: str):
    """Get player stats against different bowling types"""
    if batter_vs_bowler_data is None:
        # Return default stats if data not loaded
        return {
            "player": player_name,
            "bowling_stats": {
                "Left arm pace": 130.0,
                "Right arm pace": 125.0,
                "Off spin": 115.0,
                "Leg spin": 120.0,
                "Slow left arm orthodox": 110.0,
                "Left arm wrist spin": 118.0
            },
            "overall_averages": OVERALL_BOWLING_AVERAGES.get("batter", {
                "Left arm pace": 128.5,
                "Right arm pace": 127.2,
                "Off spin": 118.3,
                "Leg spin": 122.1,
                "Slow left arm orthodox": 112.8,
                "Left arm wrist spin": 120.4
            })
        }
    
    player_stats = batter_vs_bowler_data[batter_vs_bowler_data['Batter_Name'] == player_name]
    
    if player_stats.empty:
        # Return default stats if player not found
        return {
            "player": player_name,
            "bowling_stats": {
                "Left arm pace": 130.0,
                "Right arm pace": 125.0,
                "Off spin": 115.0,
                "Leg spin": 120.0,
                "Slow left arm orthodox": 110.0,
                "Left arm wrist spin": 118.0
            },
            "overall_averages": OVERALL_BOWLING_AVERAGES.get("batter", {
                "Left arm pace": 128.5,
                "Right arm pace": 127.2,
                "Off spin": 118.3,
                "Leg spin": 122.1,
                "Slow left arm orthodox": 112.8,
                "Left arm wrist spin": 120.4
            })
        }
    
    bowling_stats = {}
    detailed_stats = {}
    for _, row in player_stats.iterrows():
        bowling_type = row['bowler.type']
        runs = int(row['runs_vs_type']) if pd.notna(row['runs_vs_type']) else 0
        balls = int(row['balls_faced']) if pd.notna(row['balls_faced']) else 0
        strike_rate = (runs / balls * 100) if balls > 0 else 0
        avg = float(row['batting_avg']) if pd.notna(row['batting_avg']) else 0
        boundary_pct = float(row['boundary_pct']) if pd.notna(row['boundary_pct']) else 0
        dot_pct = float(row['dot_pct']) if pd.notna(row['dot_pct']) else 0
        
        bowling_stats[bowling_type] = strike_rate
        detailed_stats[bowling_type] = {
            "runs": runs,
            "balls": balls,
            "strike_rate": strike_rate,
            "average": avg,
            "boundary_pct": boundary_pct,
            "dot_pct": dot_pct
        }
    
    return {
        "player": player_name,
        "bowling_stats": bowling_stats,
        "detailed_stats": detailed_stats,
        "overall_averages": OVERALL_BOWLING_AVERAGES.get("batter", {
            "Left arm pace": 128.5,
            "Right arm pace": 127.2,
            "Off spin": 118.3,
            "Leg spin": 122.1,
            "Slow left arm orthodox": 112.8,
            "Left arm wrist spin": 120.4
        })
    }

@app.get("/team/{team_name}/bowling-stats")
async def get_team_bowling_stats(team_name: str):
    """Get team stats against different bowling types"""
    if team_vs_bowler_data is None:
        # Return default stats if data not loaded
        return {
            "team": team_name,
            "bowling_stats": {
                "Left arm pace": 135.0,
                "Right arm pace": 132.0,
                "Off spin": 125.0,
                "Leg spin": 128.0,
                "Slow left arm orthodox": 120.0,
                "Left arm wrist spin": 126.0
            },
            "overall_averages": OVERALL_BOWLING_AVERAGES.get("team", {
                "Left arm pace": 133.2,
                "Right arm pace": 130.8,
                "Off spin": 123.5,
                "Leg spin": 126.7,
                "Slow left arm orthodox": 118.9,
                "Left arm wrist spin": 124.3
            })
        }
    
    team_stats = team_vs_bowler_data[team_vs_bowler_data['batting_team'] == team_name]
    
    if team_stats.empty:
        # Return default stats if team not found
        return {
            "team": team_name,
            "bowling_stats": {
                "Left arm pace": 135.0,
                "Right arm pace": 132.0,
                "Off spin": 125.0,
                "Leg spin": 128.0,
                "Slow left arm orthodox": 120.0,
                "Left arm wrist spin": 126.0
            },
            "overall_averages": OVERALL_BOWLING_AVERAGES.get("team", {
                "Left arm pace": 133.2,
                "Right arm pace": 130.8,
                "Off spin": 123.5,
                "Leg spin": 126.7,
                "Slow left arm orthodox": 118.9,
                "Left arm wrist spin": 124.3
            })
        }
    
    bowling_stats = {}
    detailed_stats = {}
    for _, row in team_stats.iterrows():
        bowling_type = row['bowling_type']
        bowling_stats[bowling_type] = row['strike_rate']
        detailed_stats[bowling_type] = {
            "runs": int(row['total_runs']),
            "balls": int(row['total_balls'])
        }
    
    return {
        "team": team_name,
        "bowling_stats": bowling_stats,
        "detailed_stats": detailed_stats,
        "overall_averages": OVERALL_BOWLING_AVERAGES.get("team", {
            "Left arm pace": 133.2,
            "Right arm pace": 130.8,
            "Off spin": 123.5,
            "Leg spin": 126.7,
            "Slow left arm orthodox": 118.9,
            "Left arm wrist spin": 124.3
        })
    }

@app.get("/team/{team_name}/over-by-over")
async def get_team_over_by_over(team_name: str):
    """Get over-by-over bowling breakdown for a specific team"""
    if over_by_over_data is None:
        raise HTTPException(status_code=500, detail="Over-by-over data not loaded")
    
    # Filter data for the selected team
    team_bowlers = over_by_over_data[over_by_over_data['Team'] == team_name]
    
    if team_bowlers.empty:
        raise HTTPException(status_code=404, detail=f"No over-by-over data found for team: {team_name}")
    
    # Prepare data for stacked bar chart
    over_columns = [f'ov_{i:02d}' for i in range(1, 21)]  # ov_01 to ov_20
    
    result = {
        "team": team_name,
        "overs_data": []
    }
    
    # Process each over
    for i, over_col in enumerate(over_columns, 1):
        over_data = {
            "over": i,
            "bowlers": []
        }
        
        # Get all bowlers who bowled in this over
        over_bowlers = team_bowlers[team_bowlers[over_col] > 0]
        
        for _, bowler in over_bowlers.iterrows():
            over_data["bowlers"].append({
                "name": bowler['full.name'],
                "overs": int(bowler[over_col]),
                "type": bowler['bowler_category'] if pd.notna(bowler['bowler_category']) else 'Unknown',
                "bowler_type": bowler['bowler.type'] if pd.notna(bowler['bowler.type']) else 'Unknown'
            })
        
        # Sort bowlers by number of overs (descending)
        over_data["bowlers"].sort(key=lambda x: x["overs"], reverse=True)
        
        result["overs_data"].append(over_data)
    
    return result

@app.get("/team/{team_name}/pacer-spinner-breakdown")
async def get_team_pacer_spinner_breakdown(team_name: str):
    """Get pacer vs spinner breakdown for each over for a specific team"""
    if over_by_over_data is None:
        raise HTTPException(status_code=500, detail="Over-by-over data not loaded")
    
    # Filter data for the selected team
    team_bowlers = over_by_over_data[over_by_over_data['Team'] == team_name]
    
    if team_bowlers.empty:
        raise HTTPException(status_code=404, detail=f"No over-by-over data found for team: {team_name}")
    
    # Prepare data for pacer vs spinner breakdown
    over_columns = [f'ov_{i:02d}' for i in range(1, 21)]  # ov_01 to ov_20
    
    result = {
        "team": team_name,
        "overs_data": []
    }
    
    # Process each over to get pacer vs spinner breakdown
    for i, over_col in enumerate(over_columns, 1):
        over_data = {
            "over": i,
            "pacer_overs": 0,
            "spinner_overs": 0,
            "total_overs": 0
        }
        
        # Get all bowlers who bowled in this over
        over_bowlers = team_bowlers[team_bowlers[over_col] > 0]
        
        for _, bowler in over_bowlers.iterrows():
            overs = int(bowler[over_col])
            bowler_category = bowler['bowler_category'] if pd.notna(bowler['bowler_category']) else 'Unknown'
            
            if bowler_category == 'Pacer':
                over_data["pacer_overs"] += overs
            elif bowler_category == 'Spinner':
                over_data["spinner_overs"] += overs
            # Unknown bowlers are not counted in either category
            
            over_data["total_overs"] += overs
        
        result["overs_data"].append(over_data)
    
    return result

@app.get("/player/{player_name}/dismissal-locations")
async def get_player_dismissal_locations(player_name: str):
    """Get dismissal location data for a specific player"""
    if dismissal_location_data is None:
        raise HTTPException(status_code=500, detail="Dismissal location data not loaded")
    
    # Filter data for the selected player
    player_dismissals = dismissal_location_data[dismissal_location_data['Batter_Name'] == player_name]
    
    if player_dismissals.empty:
        # Return empty data if player not found
        return {
            "player": player_name,
            "dismissal_locations": [],
            "total_dismissals": 0
        }
    
    # Prepare dismissal location data
    dismissal_locations = []
    total_dismissals = 0
    
    for _, row in player_dismissals.iterrows():
        location = row['where_caught']
        count = int(row['count_of_where_caught'])
        
        dismissal_locations.append({
            "position": location,
            "count": count
        })
        total_dismissals += count
    
    # Sort by count (descending)
    dismissal_locations.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "player": player_name,
        "dismissal_locations": dismissal_locations,
        "total_dismissals": total_dismissals
    }

@app.get("/player/{player_name}/strike-rate-zones")
async def get_player_strike_rate_zones(player_name: str):
    """Get strike rate zones data for a specific player"""
    if batter_strike_rate_zones_data is None:
        raise HTTPException(status_code=500, detail="Strike rate zones data not loaded")
    
    # Filter data for the selected player
    player_zones = batter_strike_rate_zones_data[batter_strike_rate_zones_data['Batter_Name'] == player_name]
    
    if player_zones.empty:
        # Return empty data if player not found
        return {
            "player": player_name,
            "zones": [],
            "summary": {
                "total_balls": 0,
                "total_runs": 0,
                "overall_sr": 0,
                "best_zone": None
            }
        }
    
    # Prepare zones data
    zones = []
    total_balls = 0
    total_runs = 0
    best_sr = 0
    best_zone = None
    
    for _, row in player_zones.iterrows():
        line_bin = row['line_bin']
        length_bin = row['length_bin']
        balls = int(row['Balls'])
        runs = int(row['Runs'])
        strike_rate = float(row['SR'])
        
        zones.append({
            "line_bin": line_bin,
            "length_bin": length_bin,
            "balls": balls,
            "runs": runs,
            "SR": strike_rate
        })
        
        total_balls += balls
        total_runs += runs
        
        # Track best zone (minimum 10 balls for significance)
        if balls >= 10 and strike_rate > best_sr:
            best_sr = strike_rate
            best_zone = f"{length_bin} ({line_bin})"
    
    # Calculate overall strike rate
    overall_sr = (total_runs / total_balls * 100) if total_balls > 0 else 0
    
    return {
        "player": player_name,
        "zones": zones,
        "summary": {
            "total_balls": total_balls,
            "total_runs": total_runs,
            "overall_sr": round(overall_sr, 2),
            "best_zone": best_zone
        }
    }

# Venue name mapping to handle differences between app names and CSV names
def map_venue_name(venue_name: str) -> str:
    """Map application venue names to CSV venue names"""
    venue_mapping = {
        "M. A. Chidambaram Stadium, Chennai": "MA Chidambaram Stadium, Chepauk, Chennai",
        "M. Chinnaswamy Stadium, Bangalore": "M Chinnaswamy Stadium, Bengaluru",
        "Punjab Cricket Association IS Bindra Stadium, Mohali": "Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh",
        "Rajiv Gandhi International Stadium, Hyderabad": "Rajiv Gandhi International Stadium, Uppal, Hyderabad"
    }
    return venue_mapping.get(venue_name, venue_name)

@app.get("/venue/{venue_name}/toss-decisions")
async def get_venue_toss_decisions(venue_name: str):
    """Get toss decision data for a specific venue"""
    if venue_toss_decisions_data is None:
        raise HTTPException(status_code=500, detail="Venue toss decisions data not loaded")
    
    # Map venue name to CSV format
    mapped_venue_name = map_venue_name(venue_name)
    
    # Filter data for the selected venue
    venue_toss = venue_toss_decisions_data[venue_toss_decisions_data['venue_clean'] == mapped_venue_name]
    
    if venue_toss.empty:
        # Return empty data if venue not found
        return {
            "venue": venue_name,
            "toss_decisions": []
        }
    
    # Prepare toss decisions data
    toss_decisions = []
    
    for _, row in venue_toss.iterrows():
        toss_decisions.append({
            "toss": row['Toss'],
            "batted_first": int(row['Batted First']),
            "bowled_first": int(row['Bowled First'])
        })
    
    return {
        "venue": venue_name,
        "toss_decisions": toss_decisions
    }

@app.get("/venue/{venue_name}/toss-situation-details")
async def get_venue_toss_situation_details(venue_name: str):
    """Get toss situation details for a specific venue"""
    if venue_toss_situation_data is None:
        raise HTTPException(status_code=500, detail="Venue toss situation data not loaded")
    
    # Map venue name to CSV format
    mapped_venue_name = map_venue_name(venue_name)
    
    # Filter data for the selected venue
    venue_situations = venue_toss_situation_data[venue_toss_situation_data['venue_clean'] == mapped_venue_name]
    
    if venue_situations.empty:
        # Return empty data if venue not found
        return {
            "venue": venue_name,
            "situation_details": []
        }
    
    # Prepare situation details data
    situation_details = []
    
    for _, row in venue_situations.iterrows():
        situation_details.append({
            "situation": row['situation'],
            "losses": int(row['Losses']),
            "no_result": int(row['No Result']),
            "wins": int(row['Wins'])
        })
    
    return {
        "venue": venue_name,
        "situation_details": situation_details
    }

# NBA API Endpoints
@app.get("/nba/teams")
async def get_nba_teams():
    """Get list of NBA teams (Lakers and Mavericks only)"""
    return {
        "teams": ["Lakers", "Mavericks"]
    }

@app.get("/player/{player_name}/wagon-wheel")
async def get_player_wagon_wheel(player_name: str):
    """Get wagon wheel data for a specific player showing boundaries in each zone"""
    if batter_wagon_wheel_data is None:
        raise HTTPException(status_code=500, detail="Wagon wheel data not loaded")
    
    # Filter data for the selected player
    player_wagon = batter_wagon_wheel_data[batter_wagon_wheel_data['Batter_Name'] == player_name]
    
    if player_wagon.empty:
        # Return empty data if player not found
        return {
            "player_name": player_name,
            "zones": [],
            "total_boundaries": 0,
            "summary": {
                "most_productive_zone": None,
                "least_productive_zone": None,
                "zones_with_data": 0
            }
        }
    
    # Convert to list of zone dictionaries
    zones = []
    for _, row in player_wagon.iterrows():
        zones.append({
            "field_zone": str(row['field_zone']),
            "n_boundaries": int(row['n_boundaries'])
        })
    
    # Calculate summary statistics
    total_boundaries = int(player_wagon['n_boundaries'].sum())
    most_productive = player_wagon.loc[player_wagon['n_boundaries'].idxmax()]
    least_productive = player_wagon.loc[player_wagon['n_boundaries'].idxmin()]
    
    return {
        "player_name": player_name,
        "zones": zones,
        "total_boundaries": total_boundaries,
        "summary": {
            "most_productive_zone": str(most_productive['field_zone']),
            "most_productive_boundaries": int(most_productive['n_boundaries']),
            "least_productive_zone": str(least_productive['field_zone']),
            "least_productive_boundaries": int(least_productive['n_boundaries']),
            "zones_with_data": len(zones)
        }
    }

@app.get("/nba/team/{team_name}/stats")
async def get_nba_team_stats(team_name: str):
    """Get NBA team statistics"""
    if nba_team_stats_data is None:
        raise HTTPException(status_code=500, detail="NBA team stats data not loaded")
    
    # Map team names
    team_mapping = {
        "Lakers": "Los Angeles",
        "Mavericks": "Dallas"
    }
    
    mapped_team = team_mapping.get(team_name)
    if not mapped_team:
        raise HTTPException(status_code=404, detail=f"Team {team_name} not found")
    
    # Filter data for the selected team
    team_stats = nba_team_stats_data[nba_team_stats_data['team_name'] == mapped_team]
    
    if team_stats.empty:
        raise HTTPException(status_code=404, detail=f"No data found for team {team_name}")
    
    # Convert to dictionary
    team_row = team_stats.iloc[0]
    return {
        "team_name": team_name,
        "games_played": int(team_row['games_played']),
        "avg_pts_q1": float(team_row['avg_pts_q1']),
        "avg_pts_q2": float(team_row['avg_pts_q2']),
        "avg_pts_q3": float(team_row['avg_pts_q3']),
        "avg_pts_q4": float(team_row['avg_pts_q4']),
        "avg_pts_h1": float(team_row['avg_pts_h1']),
        "avg_pts_h2": float(team_row['avg_pts_h2']),
        "avg_pts_conc_q1": float(team_row['avg_pts_conc_q1']),
        "avg_pts_conc_q2": float(team_row['avg_pts_conc_q2']),
        "avg_pts_conc_q3": float(team_row['avg_pts_conc_q3']),
        "avg_pts_conc_q4": float(team_row['avg_pts_conc_q4']),
        "avg_pts_conc_h1": float(team_row['avg_pts_conc_h1']),
        "avg_pts_conc_h2": float(team_row['avg_pts_conc_h2']),
        "wins_when_leading_q1": int(team_row['wins_when_leading_q1']),
        "wins_when_trailing_q1": int(team_row['wins_when_trailing_q1']),
        "avg_win_margin": float(team_row['avg_win_margin']),
        "avg_loss_margin": float(team_row['avg_loss_margin']),
        "avg_diff_q1": float(team_row['avg_diff_q1']),
        "avg_diff_q2": float(team_row['avg_diff_q2']),
        "avg_diff_q3": float(team_row['avg_diff_q3']),
        "avg_diff_q4": float(team_row['avg_diff_q4'])
    }

@app.get("/nba/team/{team_name}/players")
async def get_nba_team_players(team_name: str):
    """Get list of players for a specific NBA team"""
    if nba_player_stats_data is None:
        raise HTTPException(status_code=500, detail="NBA player stats data not loaded")
    
    # Map team names
    team_mapping = {
        "Lakers": "Lakers",
        "Mavericks": "Mavericks"
    }
    
    mapped_team = team_mapping.get(team_name)
    if not mapped_team:
        raise HTTPException(status_code=404, detail=f"Team {team_name} not found")
    
    # Filter players for the selected team
    team_players = nba_player_stats_data[nba_player_stats_data['team'] == mapped_team]
    
    if team_players.empty:
        return {"team": team_name, "players": []}
    
    # Get unique player names
    players = team_players['player_name'].unique().tolist()
    
    return {
        "team": team_name,
        "players": sorted(players)
    }

@app.get("/nba/player/{player_name}/stats")
async def get_nba_player_stats(player_name: str):
    """Get NBA player statistics"""
    if nba_player_stats_data is None:
        raise HTTPException(status_code=500, detail="NBA player stats data not loaded")
    
    # Filter data for the selected player
    player_stats = nba_player_stats_data[nba_player_stats_data['player_name'] == player_name]
    
    if player_stats.empty:
        raise HTTPException(status_code=404, detail=f"No data found for player {player_name}")
    
    # Convert to dictionary
    player_row = player_stats.iloc[0]
    return {
        "player_name": player_name,
        "team": str(player_row['team']),
        "games_played_window": int(player_row['games_played_window']),
        "avg_points_q1_per_game": float(player_row['avg_points_q1_per_game']),
        "avg_points_q2_per_game": float(player_row['avg_points_q2_per_game']),
        "avg_points_q3_per_game": float(player_row['avg_points_q3_per_game']),
        "avg_points_q4_per_game": float(player_row['avg_points_q4_per_game']),
        "avg_points_first_half_per_game": float(player_row['avg_points_first_half_per_game']),
        "avg_points_second_half_per_game": float(player_row['avg_points_second_half_per_game']),
        "points_per_game_last5": float(player_row['points_per_game_last5']) if pd.notna(player_row['points_per_game_last5']) else 0,
        "rebounds_per_game_last5": float(player_row['rebounds_per_game_last5']) if pd.notna(player_row['rebounds_per_game_last5']) else 0,
        "assists_per_game_last5": float(player_row['assists_per_game_last5']) if pd.notna(player_row['assists_per_game_last5']) else 0,
        "threes_made_per_game_last5": float(player_row['threes_made_per_game_last5']) if pd.notna(player_row['threes_made_per_game_last5']) else 0,
        "points_per_game_last10": float(player_row['points_per_game_last10']) if pd.notna(player_row['points_per_game_last10']) else 0,
        "rebounds_per_game_last10": float(player_row['rebounds_per_game_last10']) if pd.notna(player_row['rebounds_per_game_last10']) else 0,
        "assists_per_game_last10": float(player_row['assists_per_game_last10']) if pd.notna(player_row['assists_per_game_last10']) else 0,
        "threes_made_per_game_last10": float(player_row['threes_made_per_game_last10']) if pd.notna(player_row['threes_made_per_game_last10']) else 0
    }

# Pydantic models for PowerPoint generation
class SlideData(BaseModel):
    type: str
    player_name: Optional[str] = None
    team_name: Optional[str] = None
    venue_name: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None

class PPTGenerationRequest(BaseModel):
    slides: List[SlideData]
    gemini_api_key: str

@app.post("/generate-ppt")
async def generate_powerpoint(request: PPTGenerationRequest):
    """
    Generate PowerPoint presentation using Gemini AI
    
    Request body should contain:
    - slides: List of slide data (type, name, statistics)
    - gemini_api_key: Gemini API key for content generation
    """
    try:
        # Initialize Gemini PPT Generator
        generator = GeminiPPTGenerator(api_key=request.gemini_api_key)
        
        # Prepare slides data
        slides_data = []
        for slide in request.slides:
            slide_dict = slide.dict()
            
            # Fetch relevant statistics based on slide type
            if slide.type == 'player' and slide.player_name:
                # Get player bowling stats
                try:
                    player_data = batter_vs_bowler_data[
                        batter_vs_bowler_data['Striker'] == slide.player_name
                    ]
                    if not player_data.empty:
                        stats = {}
                        for _, row in player_data.iterrows():
                            bowling_type = row['Bowling_Type']
                            stats[bowling_type] = {
                                'strike_rate': float(row['Strike_Rate']),
                                'balls': int(row['Balls']),
                                'runs': int(row['Runs'])
                            }
                        slide_dict['statistics'] = stats
                except Exception as e:
                    print(f"Error fetching player stats: {e}")
                    
            elif slide.type == 'team' and slide.team_name:
                # Get team bowling stats
                try:
                    team_stats = team_vs_bowler_data[
                        team_vs_bowler_data['Team'] == slide.team_name
                    ]
                    if not team_stats.empty:
                        stats = {}
                        for _, row in team_stats.iterrows():
                            bowling_type = row['Bowling_Type']
                            stats[bowling_type] = {
                                'strike_rate': float(row['Strike_Rate']),
                                'balls': int(row['Balls']),
                                'runs': int(row['Runs'])
                            }
                        slide_dict['statistics'] = stats
                except Exception as e:
                    print(f"Error fetching team stats: {e}")
                    
            elif slide.type == 'overbyover' and slide.team_name:
                # Get over-by-over data
                try:
                    over_data = over_by_over_data[
                        over_by_over_data['Team'] == slide.team_name
                    ]
                    if not over_data.empty:
                        slide_dict['over_by_over_data'] = over_data.to_dict('records')
                except Exception as e:
                    print(f"Error fetching over-by-over data: {e}")
                    
            elif slide.type == 'venue' and slide.venue_name:
                # Get venue data
                try:
                    venue_stats = venue_data[
                        venue_data['Venue'] == slide.venue_name
                    ]
                    if not venue_stats.empty:
                        slide_dict['statistics'] = venue_stats.iloc[0].to_dict()
                except Exception as e:
                    print(f"Error fetching venue stats: {e}")
            
            slides_data.append(slide_dict)
        
        # Generate presentation
        presentation = generator.create_presentation(slides_data)
        
        # Save to BytesIO
        ppt_io = io.BytesIO()
        presentation.save(ppt_io)
        ppt_io.seek(0)
        
        # Return as streaming response
        return StreamingResponse(
            ppt_io,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": "attachment; filename=IPL_Opposition_Analysis.pptx"
            }
        )
        
    except Exception as e:
        print(f"Error generating PowerPoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating PowerPoint: {str(e)}")

@app.post("/generate-screenshot-ppt")
async def generate_screenshot_powerpoint(request: PPTGenerationRequest):
    """
    Generate PowerPoint presentation using screenshots
    Captures exact visual appearance of web app at 1920x1080 resolution
    
    Request body should contain:
    - slides: List of slide data (type, name)
    - gemini_api_key: Not used but kept for compatibility
    """
    try:
        # Determine base URL (use production URL if available, otherwise localhost)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        print(f"\n{'='*60}")
        print(f"Screenshot-based PPT Generation Request")
        print(f"Frontend URL: {frontend_url}")
        print(f"Number of slides: {len(request.slides)}")
        print(f"{'='*60}\n")
        
        # Initialize Screenshot PPT Generator
        generator = ScreenshotPPTGenerator(base_url=frontend_url)
        
        # Prepare slides data
        slides_data = []
        for slide in request.slides:
            slide_dict = slide.dict()
            slides_data.append(slide_dict)
            print(f"  - {slide_dict.get('type')}: {slide_dict.get('player_name') or slide_dict.get('team_name') or slide_dict.get('venue_name')}")
        
        # Generate presentation (async)
        presentation = await generator.create_presentation(slides_data)
        
        # Save to BytesIO
        ppt_io = io.BytesIO()
        presentation.save(ppt_io)
        ppt_io.seek(0)
        
        print(f"\n✓ PowerPoint file ready for download\n")
        
        # Return as streaming response
        return StreamingResponse(
            ppt_io,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": "attachment; filename=IPL_Opposition_Analysis_Screenshots.pptx"
            }
        )
        
    except Exception as e:
        print(f"\n✗ Error generating PowerPoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating PowerPoint: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
