from sqlalchemy import Column, Integer,String,Float,Boolean,DateTime,Text,ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base= declarative_base()

#Table 1 : Games 
#Every Chess game played gets one row here

class Game(Base):
    __tablename__="games"

    id=Column(Integer,primary_key=True,index=True)
    session_id=Column(String,index=True)  #Who Played
    result = Column(String)  # While , Black , Draw
    winner = Column(String)  # Human, AI, Draw
    total_moves=Column(Integer,default =0) 
    duration_secs=Column(Integer,default=0)  #How long the game took
    ai_version=Column(Integer,default=1)  #Which version of AI played
    created_at=Column(DateTime,default=datetime.utcnow)

    #One game has many moves 
    moves=relationship("Move",back_populates="game")

#Table 2 : Moves
#Every move in a chess game gets one row here
class Move(Base):
    __tablename__="moves"
    
    id  =Column(Integer,primary_key=True,index=True)
    game_id =Column(Integer,ForeignKey("games.id"))
    move_number =Column(Integer)  #move 1,2,3
    player =Column(String)  #Human or AI
    move_uci=Column(String)  #Move in UCI format e.g. e2e4, g8f6
    fen_before=Column(Text)  #Board state before the move (FEN format)
    fen_after=Column(Text)      #Board state after the move (FEN format)
    reward=Column(Float, default=0.0)  #Reward for this move (for RL training)
    created_at=Column(DateTime,default=datetime.utcnow)

    game=relationship("Game",back_populates="moves")



#table 3 : Active Sessions

#Who is playing Righht now - shown on live dashboards

class ActiveSession(Base):
    __tablename__="active_sessions"

    id =Column(Integer,primary_key=True,index=True)
    session_id =Column(String,unique=True,index=True)  #Unique ID for the session
    player_name =Column(String,default="Anonymous")  #Player's name (optional
    current_move = Column(Integer,default=0) #Current move number in the ongoing game
    started_at = Column(DateTime,default=datetime.utcnow) #When the session started
    last_seen = Column(DateTime,default=datetime.utcnow) #Last time the player made a move or interacted
    is_active = Column(Boolean,default=True) #Is the session currently active



#Table 4 : Model Metrics
#Ai Report Card - tracked after every game
class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id              = Column(Integer, primary_key=True, index=True)
    ai_version      = Column(Integer)                   # v1, v2, v3...
    total_games     = Column(Integer, default=0)
    wins            = Column(Integer, default=0)
    losses          = Column(Integer, default=0)
    draws           = Column(Integer, default=0)
    win_rate        = Column(Float, default=0.0)        # wins/total_games
    avg_reward      = Column(Float, default=0.0)        # average RL reward
    avg_game_length = Column(Float, default=0.0)        # longer = smarter
    recorded_at     = Column(DateTime, default=datetime.utcnow)
