from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

app = FastAPI(title="IPL Opposition Planning API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data directory path
DATA_DIR = Path(__file__).parent / "data"

# Team players mapping
TEAM_PLAYERS = {
    'Chennai Super Kings': [
        'Ruturaj Gaikwad', 'Devon Conway', 'Ravindra Jadeja', 
        'Mahendra Singh Dhoni', 'Shivam Dube', 'Moeen Ali', 'Deepak Chahar', 
        'Dwayne Bravo', 'Tushar Deshpande'
    ],
    'Mumbai Indians': [
        'Ishan Kishan', 'Suryakumar Yadav', 'Tilak Varma', 'Tim David',
        'Hardik Pandya', 'Rohit Sharma', 'Jasprit Bumrah', 
        'Rahul Chahar', 'Tymal Mills', 'Kieron Pollard'
    ],
    'Royal Challengers Bangalore': [
        'Virat Kohli', 'Faf du Plessis', 'Glenn Maxwell', 'Dinesh Karthik',
        'Rajat Patidar', 'AB de Villiers', 'Wanindu Hasaranga', 'Harshal Patel', 
        'Mohammed Siraj', 'Josh Hazlewood', 'Akash Deep'
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
        'Kane Williamson', 'Aiden Markram', 'Nicholas Pooran',
        'Abdul Samad', 'Abhishek Sharma', 'Washington Sundar', 'Bhuvneshwar Kumar', 
        'T Natarajan', 'Umran Malik', 'Marco Jansen', 'Travis Head'
    ],
    'Gujarat Titans': [
        'David Miller', 'Sai Sudharsan',
        'Rahul Tewatia', 'Wriddhiman Saha', 'Rashid Khan', 'Mohammed Shami', 
        'Lockie Ferguson', 'Alzarri Joseph', 'Yash Dayal'
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

@app.get("/")
async def root():
    return {"message": "IPL Opposition Planning API is running!"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
