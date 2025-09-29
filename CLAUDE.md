# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

**Universal Adaptive Combat AI Framework**: Create a plug-and-play AI system that can be integrated into any combat-oriented game to make enemies adapt to individual player behavior patterns in real-time.

### Core Concept
The framework will act as a "player behavior classifier" + "strategic response system" that:
1. Receives standardized player behavior data from any game
2. Classifies player patterns (aggressive vs defensive, risk-taking vs conservative, spatial preferences, etc.)
3. Returns high-level strategic recommendations (not specific actions)
4. Learns universal combat psychology patterns, not game-specific mechanics

### Vision
Enable game developers to integrate adaptive AI without custom programming by providing a universal abstraction layer that works across different games.

## Current Project Status: Phase 1 (Proof of Concept)

The current codebase is the Phase 1 implementation - a simple combat game built specifically for data collection and initial behavior classification testing.

**Purpose of current implementation**:
- Collect diverse gameplay data from different player styles
- Test basic player behavior classification (aggressive, defensive, etc.)
- Validate that AI can adapt to player patterns
- Generate training data for machine learning models

This is **NOT** the final product - it's a testing ground for the universal framework that will be built in later phases.

## Development Phases

### Phase 1: Proof of Concept (Months 1-4) ← CURRENT PHASE
- Build simple combat game for testing (✓ `game.py`)
- Implement data collection system (✓ `DataLogger`)
- Create basic player behavior classification (3-4 categories)
- Prove AI can adapt to different player styles
- **Success criteria**: AI demonstrably changes behavior based on player patterns

### Phase 2: Framework Development (Months 5-8)
- Design standardized input/output formats for any game
- Create Universal Game State Abstraction Layer
- Expand classification categories (10+ behavior types)
- Build Game Integration API
- Test with 2-3 different simple games
- **Success criteria**: Same AI works across multiple different game types

### Phase 3: Real-World Integration (Months 9-12)
- Build integration tools for major game engines (Unity, Unreal, Godot)
- Optimize for real-time performance (sub-millisecond response times)
- Test with existing games/demos
- Refine classification accuracy
- **Success criteria**: Seamless integration with professional game engines

### Phase 4: Advanced Features (Months 13-18)
- Multi-player adaptation (enemies learn from multiple players)
- Long-term player modeling (remembers players across sessions)
- Advanced strategic reasoning
- Performance analytics and debugging tools
- **Success criteria**: Production-ready system for commercial games

## Core Components (To Be Built)

1. **Player Behavior Classification System**: ML models that analyze player actions and categorize behavioral patterns
2. **Universal Game State Abstraction Layer**: Converts game-specific data into standardized format
3. **Strategic Response Engine**: Takes player classifications and generates counter-strategies
4. **Game Integration API**: Standardized interface for games to communicate with the AI

## Current Implementation Overview

This is a Python-based adaptive combat AI game with data collection capabilities. It's a top-down shooter built with Pygame where the player fights waves of enemies while the system logs gameplay data for AI training purposes.

## Running the Game

```bash
python game.py
```

The game runs immediately without additional setup steps. Requires dependencies from `requirements.txt` (currently just pygame).

## Core Architecture

### Main Game Loop (Game class)
- Entry point: `game.py:497` (`if __name__ == "__main__"`)
- Game loop: `game.py:462-495` (`Game.run()`)
- Frame rate: 60 FPS constant
- Delta time-based updates for consistent physics

### Entity System
All entities (Player, Enemy, Bullet, CoverObject) follow the same pattern:
- Constructor sets initial state and properties
- `update(dt, ...)` method for game logic
- `draw(screen)` method for rendering

**Player** (`game.py:116-205`):
- Movement: WASD or arrow keys, normalized diagonal movement
- Shooting: Mouse aim + left click, cooldown-based firing
- Screen boundary clamping

**Enemy** (`game.py:207-275`):
- Two AI types: "basic" (aggressive) and "sniper" (maintains distance)
- AI behavior in `update()`: distance-based movement decisions
- Autonomous shooting with cooldowns

**Bullet** (`game.py:95-114`):
- Owner tracking ("player" vs "enemy") for collision logic
- Fixed speed, angle-based trajectory
- Color-coded by owner (yellow=player, red=enemy)

### Data Collection System (DataLogger class)

The DataLogger (`game.py:27-93`) is central to this project's purpose - collecting training data for AI:

**Event logging**: Discrete events (shots, damage, deaths, waves) via `log_event()`
- Shot fired with position, angle, target, ammo
- Damage taken/dealt with health and position
- Enemy kills with type and location
- Wave completions

**Frame-by-frame metrics** (`log_frame_data()`): Sampled every 10 frames
- Player position
- Enemy count and distances (average + nearest)
- Proximity to cover
- Player health

**Session data structure**:
```python
{
  'session_id': timestamp,
  'events': [],                    # Discrete events
  'behavioral_metrics': [],         # Frame samples
  'player_stats': {                 # Aggregate statistics
    'total_damage_dealt': 0,
    'total_damage_taken': 0,
    'shots_fired': 0,
    'shots_hit': 0,
    'enemies_killed': 0,
    'distance_traveled': 0
  }
}
```

**Data output**: JSON file saved on game exit with filename `gameplay_data_{timestamp}.json`

### Collision System

Located in `Game.handle_collisions()` (`game.py:340-368`):
- Circle-to-circle collision detection (radius-based)
- Three collision types: bullet-enemy, bullet-player, bullet-cover
- Damage application and stat tracking on collision
- Bullet removal after collision

### Wave System

Progressive difficulty (`game.py:402-407`):
- Starts at wave 1 with 3 enemies
- Increases to max 6 enemies per wave
- Wave advances when all enemies defeated
- Game ends at wave 10 or player death

## Key Constants

- Screen: 1024x768 pixels
- Player speed: 200 units/second
- Player health: 100, bullet damage from enemies: 15
- Enemy health: 30, bullet damage to enemies: 10
- Bullet speeds: Player=500, Enemy=300

## Controls

- **WASD/Arrow keys**: Movement
- **Mouse**: Aim direction
- **Left click**: Shoot
- **ESC**: Quit and save data

## Data Logging Integration

When modifying gameplay mechanics, ensure proper logging:
1. Call `data_logger.log_event()` for significant actions
2. Update `player_stats` dictionary for trackable metrics
3. Pass `data_logger` to methods that trigger loggable events
4. Example pattern: `game.py:157-176` (player shooting)