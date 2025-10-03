# CLAUDE.md - AI Assistant Context

## What This Project Actually Is

**Persistent Player Modeling System**: A universal AI framework that learns player combat behavior over many sessions and adapts enemy tactics based on accumulated knowledge.

### Critical Understanding: NOT Live Inference

❌ **This is NOT**:
- Real-time reactive AI that changes behavior mid-match
- Live inference system during gameplay
- Game-specific adaptive AI
- Immediate pattern recognition

✅ **This IS**:
- Netflix-style recommendation system for enemy behavior
- Long-term player profiling across sessions
- Hierarchical classification that deepens over time (Tier 1 → 2 → 3 → 4)
- Universal abstraction layer that works across different combat games
- Between-session adaptation, not within-match changes

**Key Analogy**: Doctor reviewing entire medical history over years vs. 5-minute diagnosis

---

## Current Phase: Phase 1 (Proof of Concept)

### What Phase 1 Is For
- **Primary Goal**: Collect quality gameplay data and prove basic classification works
- **Secondary Goal**: Build foundation for universal abstraction layer
- **NOT the goal**: Build the final product or perfect the game

### Current Implementation: `game.py`
**Purpose**: Data collection training ground, NOT the final product

The game is intentionally simple:
- Top-down shooter with wave-based survival
- Basic enemy types (aggressive "basic", ranged "sniper")
- Comprehensive telemetry logging via `DataLogger`
- 5-10 minute sessions for rapid data collection

**Remember**: Game features should serve data collection, not vice versa

### What We're Building Toward (Phase 1)
1. LSTM session encoder (compress each match → 256D embedding)
2. Tier 1 classifier using Random Forest (5 categories: Aggressive, Defensive, Tactical, Mobile, Chaotic)
3. Dataset: 5,000+ sessions from 100+ players
4. Basic enemy adaptation based on Tier 1 classification
5. **Success**: 70%+ accuracy on broad playstyle classification

---

## Technical Architecture (Simplified)

### The Flow
```
Session Data → LSTM Encoder → Session Embedding (256D)
                                      ↓
Player History (N sessions) → Transformer → Player Profile (768D)
                                      ↓
              Hierarchical Classifiers → Enemy Adaptation Params
```

### Phase-by-Phase Model Evolution

**Phase 1** (Current):
- Manual feature engineering
- LSTM for session encoding
- Random Forest for Tier 1 classification
- Rule-based adaptation

**Phase 2** (Months 4-6):
- Transformer for cross-session learning
- Tier 2 hierarchical classification
- Persistent storage (PostgreSQL + vector DB)

**Phase 3+** (Later):
- Tier 3 specializations
- Micro-preference detection
- Transfer learning to other games

### Universal Abstraction Principle

All metrics must be **normalized and game-agnostic**:
- "Engagement distance = 85th percentile" (not "150 pixels")
- "Pursuit ratio = 25%" (% time moving toward enemies)
- "Cover dependency = 60%" (% combat time behind cover)

**Why**: These translate across FPS, top-down, RPG, strategy games

---

## Data Requirements (Phase 1)

### Core Data Streams
Collect every 10-20 frames:

**Spatial**:
- Player position (x, y)
- Enemy positions (all active)
- Facing direction / aim vector
- Movement velocity

**Combat**:
- Shot fired (position, angle, target, hit/miss)
- Damage dealt/taken (amount, source)
- Reload events (timing, ammo state)
- Enemy kills (location, time, weapon type)

**Tactical**:
- Cover usage (in/out, duration)
- Health/ammo pickups (timing, state when collected)
- Zone control (time in map areas)

**Outcome**:
- Match duration, score, win/loss
- Session metadata (timestamp, player ID)

### Derived Features (Compute Post-Match)
- Average engagement distance
- Kill/Death ratio
- Damage per second
- Accuracy percentage
- Time in combat vs exploration
- Aggression curve over match
- Movement patterns (static vs mobile)

---

## Current Implementation Details

### File: `game.py`

**DataLogger class** (`game.py:27-93`):
- Central to project purpose
- `log_event()`: Discrete actions (shots, damage, kills, waves)
- `log_frame_data()`: Continuous metrics (sampled every 10 frames)
- Output: JSON file `gameplay_data_{timestamp}.json`

**Game Loop** (`game.py:462-495`):
- 60 FPS, delta time-based updates
- Frame sampling for behavioral metrics
- Session boundaries: Game start → player death/wave 10

**Entity System**:
- **Player** (`game.py:116-205`): WASD movement, mouse aim/shoot
- **Enemy** (`game.py:207-275`): Two AI types (basic=aggressive, sniper=distance)
- **Bullet** (`game.py:95-114`): Owner tracking for collision logic

**Wave System** (`game.py:402-407`):
- Progressive difficulty: 3 → 6 enemies max
- Natural session boundaries for data collection
- Ends at wave 10 or player death

### When Modifying Game Mechanics

**Always ensure**:
1. New actions logged via `data_logger.log_event()`
2. Relevant stats updated in `player_stats` dictionary
3. Frame-level metrics captured if spatially/temporally relevant
4. Focus on data quality, not game polish

**Pattern**: See `game.py:157-176` (player shooting) for logging integration example

---

## Development Priorities (Phase 1)

### Focus On
1. **Data quality**: Clean, consistent, comprehensive logging
2. **Archetype separation**: Game mechanics that reveal distinct playstyles
3. **Session diversity**: Encourage different player behaviors
4. **Volume**: Get to 5,000+ sessions quickly

### Avoid
1. ❌ Over-engineering the game (graphics, UI, features)
2. ❌ Adding mechanics that don't contribute to classification
3. ❌ Optimizing for fun over data collection
4. ❌ Building live inference features (not the goal!)
5. ❌ Game-specific features that won't generalize

### Good vs Bad Features

**Good** (supports universal classification):
- Multiple weapon types (reveals range preference)
- Cover system (reveals defensive tendencies)
- Wave pressure (reveals stress response)
- Open arena (reveals spatial patterns)

**Bad** (too game-specific):
- Complex upgrade trees
- Story/narrative elements
- Intricate UI systems
- Game-specific mechanics (grappling, vehicles, etc.)

---

## Hierarchical Classification Tree

### Tier 1: Broad Playstyle (5-10 matches)
- **Aggressive**: Close-range, pursuit-focused
- **Defensive**: Long-range, retreat-focused
- **Tactical**: Cover-heavy, positioning-focused
- **Mobile**: Hit-and-run, high movement
- **Chaotic**: Inconsistent, still learning

### Tier 2: Combat Archetype (15-30 matches)
```
Aggressive → Berserker, Flanker, Rusher
Defensive → Sniper, Skirmisher, Fortress
Tactical → Ambusher, Controller, Adaptive
Mobile → Ghost, Harasser, Scout
```

### Tier 3: Specialization (50+ matches)
```
Sniper → Patient Marksman, Suppressor, Relocator
Berserker → Tank Build, Glass Cannon, Momentum Fighter
```

### Tier 4: Micro-preferences (100+ matches)
- Exact engagement distances
- Reload timing patterns
- Target selection logic
- Resource management style
- Stress responses

**Progressive refinement**: New players get Tier 1 fast, veterans get fine-grained personalization

---

## Enemy Adaptation Logic

### Phase 1: Simple Rule-Based

```python
if Tier_1 == "Aggressive":
    spawn_distance = "far"        # Make them work for it
    enemy_retreat = True          # Kite them
    use_cover = "heavy"

elif Tier_1 == "Defensive":
    spawn_distance = "close"      # Force out of comfort
    enemy_movement = "erratic"    # Hard to track
    flanking_freq = "high"        # Attack from sides
```

### Phase 2+: Parameter-Based
- Continuous values instead of binary rules
- Confidence-weighted (low confidence → generic behavior)
- Difficulty scaling based on win rate

### Phase 3+: Meta-Counters
- Counter the player's counter-strategies
- Occasional surprises (break patterns)
- Temporal awareness (fatigue, time since last session)

---

## Success Metrics (Phase 1)

### Technical
- **Tier 1 accuracy**: 70%+ after 5 matches
- **Session encoding**: <100ms per match
- **Data collection**: 5,000+ clean sessions
- **Embedding quality**: Clusters visually align with archetypes

### User Experience
- **Adaptation detection**: 60%+ players notice behavior changes
- **Archetype identification**: Players can identify their style
- **Engagement**: Session length stable/increasing over time

### Data Quality
- No missing/corrupt sessions
- Balanced archetype distribution (avoid all aggressive players)
- Clear behavioral separation in feature space

---

## Key Decisions & Constraints

### When to Add ML Models
- **Now**: Session encoder (LSTM) + Tier 1 classifier (RF)
- **Phase 2**: Transformer for player profiles
- **Phase 3+**: Advanced classifiers, transfer learning

### When to Expand Game Features
- **Only if**: It reveals new behavioral patterns for classification
- **Ask**: "Does this help distinguish Aggressive vs Defensive?"
- **Avoid**: Features for fun/polish that don't contribute to data

### When to Optimize Performance
- **Phase 1**: Don't. Data collection is the priority
- **Phase 2-3**: Once models are built
- **Phase 4**: Real-time optimization (<50ms inference)

### When to Think About Other Games
- **Not yet**: Stay focused on training game
- **Phase 4**: After Tier 3 classification works well
- **Goal**: Validate transfer learning, not build integrations

---

## How to Help the Developer

### When They Ask About Features
1. Check if it serves data collection / classification
2. Remind them: game is a tool, not the product
3. Suggest simplest implementation that gets the data

### When They Get Stuck
1. Refocus on Phase 1 goals: data + Tier 1 classification
2. Check if they're over-engineering
3. Validate current implementation meets data needs

### When They Want to Jump Ahead
1. Acknowledge the vision (it's exciting!)
2. Ground in current phase requirements
3. Emphasize: prove basics work first

### When Debugging
1. Prioritize data quality issues
2. Check logging integration
3. Ensure session boundaries are clean
4. Validate feature engineering makes sense

---

## Quick Reference

### Running the Game
```bash
python game.py
```

### Controls
- WASD/Arrows: Move
- Mouse: Aim
- Left Click: Shoot
- ESC: Quit and save data

### Data Location
`gameplay_data_{timestamp}.json`

### Key Constants
- Screen: 1024x768
- Player speed: 200 units/sec, health: 100
- Enemy health: 30, damage to player: 15
- Bullet speeds: Player=500, Enemy=300

### Important Code Locations
- DataLogger: `game.py:27-93`
- Player: `game.py:116-205`
- Enemy AI: `game.py:207-275` (see `update()` method)
- Collision handling: `game.py:340-368`
- Wave system: `game.py:402-407`

---

## Remember

**Core Philosophy**: Persistent learning beats live inference. We have unlimited time to analyze history.

**Development Mantra**: Data quality > game polish. Classification accuracy > real-time reaction.

**Phase 1 Goal**: Prove that session embeddings cluster by archetype and Tier 1 classification works.

Everything else is future work. Stay focused on the foundation.
