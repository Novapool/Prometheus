# Persistent Player Modeling System
## Building Enemies That Learn Your Playstyle Over Time

---

## 🎯 What This Project Is

**A persistent player profile system that evolves over many play sessions, creating increasingly personalized enemy behavior that adapts to individual playstyles.**

Think of it like **Netflix for enemy AI**: Instead of deciding what you like from your first 10 minutes, it learns over weeks and months. Your system learns combat behavior the same way.

### The Core Idea

You're **NOT** building:
- ❌ Real-time reactive AI that changes mid-match
- ❌ Live inference during gameplay
- ❌ Game-specific AI system

You **ARE** building:
- ✅ Persistent player profiles that deepen over time
- ✅ Hierarchical classification that becomes more specific with data
- ✅ Enemy tactics that adapt between sessions based on accumulated knowledge
- ✅ Universal system that transfers insights across different games

### Why This Matters

**For Players**: Games that feel personalized, enemies that "know" your style, increased replay value

**For Developers**: Plug-and-play adaptive AI without custom programming for each game

**For You**: Novel ML application combining game development with persistent behavioral modeling

---

## 🌳 How It Works (Simplified)

### Hierarchical Classification Tree

**Tier 1** (5-10 matches): Broad playstyle
- Aggressive, Defensive, Tactical, Mobile, Chaotic

**Tier 2** (15-30 matches): Combat archetype
- Aggressive → Berserker, Flanker, Rusher
- Defensive → Sniper, Skirmisher, Fortress
- Tactical → Ambusher, Controller, Adaptive
- Mobile → Ghost, Harasser, Scout

**Tier 3** (50+ matches): Specialization
- Sniper → Patient Marksman, Suppressor, Relocator
- Rusher → Tank Build, Glass Cannon, Momentum Fighter

**Tier 4** (100+ matches): Micro-preferences
- Exact engagement distances, reload patterns, target selection, stress responses

### Technical Architecture

```
Match Data → Session Encoder (LSTM) → Session Embedding (256D)
                                              ↓
Multiple Sessions → Transformer → Player Profile (768D)
                                              ↓
                    Hierarchical Classifiers (RF at each tier)
                                              ↓
                          Enemy Adaptation Parameters
```

### Universal Abstraction

Focus on combat psychology, not game mechanics:
- "Aggressive" means the same in any combat game
- Metrics normalized to percentages/ratios
- Works across FPS, top-down, action RPG, etc.

---

## 📅 Development Roadmap

### ✅ Phase 1: Foundation (Months 1-3) ← YOU ARE HERE

**Goal**: Prove core concept works

**Tasks**:
- ✅ Build simple combat training game (`game.py`)
- ✅ Implement comprehensive data logging (`DataLogger`)
- ⏳ Build session encoder (LSTM for match compression)
- ⏳ Create Tier 1 classifier (5 broad categories)
- ⏳ Collect 5,000+ sessions from 100 players
- ⏳ Implement basic enemy adaptation

**Success Criteria**: 70%+ accuracy distinguishing Aggressive vs Defensive vs Tactical

---

### Phase 2: Depth & History (Months 4-6)

**Goal**: Add temporal awareness and deeper classification

**Tasks**:
- Build Transformer for cross-session synthesis
- Implement Tier 2 classification (15-20 archetypes)
- Create persistent profile storage (PostgreSQL + vector DB)
- Enhanced adaptation based on Tier 2

**Success Criteria**: After 15 matches, accurate archetype classification

---

### Phase 3: Specialization (Months 7-9)

**Goal**: Fine-grained personalization

**Tasks**:
- Tier 3 classification (40-60 specializations)
- Micro-preference detection
- Advanced adaptation with meta-counters
- Cross-session learning (account for breaks, fatigue)

**Success Criteria**: 50+ matches = highly personalized enemy behavior

---

### Phase 4: Transfer Learning (Months 10-12)

**Goal**: Make it work across different games

**Tasks**:
- Build abstraction API for universal game integration
- Test in completely different game (FPS, 3D action, etc.)
- Validate classification transfer
- Create developer toolkit

**Success Criteria**: Same AI works across multiple game genres

---

### Phase 5: Production (Months 13+)

**Goal**: Commercial-ready system

**Tasks**:
- Real-time optimization (<50ms inference)
- Player-facing dashboards ("You are a Berserker (Tank Build)")
- Continuous learning pipeline
- SDK/middleware for game engines

**Success Criteria**: Production-ready for commercial games

---

## 🎮 Current Status

### What's Built
- Top-down combat training game (Wave-based survival)
- Comprehensive telemetry logging system
- Data collection for player behavior patterns
- Basic enemy AI types (aggressive, sniper)

### What You're Working On Now
**Phase 1 - Week 1-4**:
1. Refine game to have clear archetype separation
2. Collect 500 sessions from 10+ players
3. Build LSTM session encoder
4. Validate embeddings cluster by playstyle

### Next Immediate Steps
1. Test game with diverse players
2. Manually label player archetypes from gameplay
3. Engineer 20-30 features per session
4. Train initial Random Forest classifier
5. Achieve 65%+ accuracy on Tier 1

---

## 🚀 Running the Project

### Start the Training Game
```bash
python game.py
```

### Controls
- **WASD/Arrows**: Move
- **Mouse**: Aim
- **Left Click**: Shoot
- **ESC**: Quit and save data

### Data Output
Gameplay sessions saved as: `gameplay_data_{timestamp}.json`

---

## 📊 Success Metrics

### Phase 1 Targets
- **Classification**: 70%+ accuracy on Tier 1 after 5 matches
- **Data Collection**: 5,000+ sessions from 100+ unique players
- **Adaptation**: 60%+ players notice enemy behavior differences

### Long-term Targets
- **Tier 2**: 55%+ accuracy after 15 matches
- **Tier 3**: 40%+ accuracy after 50 matches
- **Engagement**: 40%+ player retention at 15+ sessions
- **Perception**: 70%+ players identify their archetype correctly

---

## 💡 Key Insights

### Why Persistent Learning > Live Inference

**Live systems**: Must decide in milliseconds with limited context
**Your system**: Unlimited time to analyze full history = better accuracy

**Analogy**: Doctor diagnosing you in 5 minutes vs. reviewing your entire medical history

### Why This Approach Works

1. **Netflix model**: Broad suggestions early → refined recommendations later
2. **Cross-session understanding**: Not reaction, but understanding who you are as a player
3. **Universal patterns**: Combat psychology transfers across game mechanics
4. **Progressive refinement**: New players get quick classification, veterans get personalization

---

## 🛠️ Technical Stack

**Current (Phase 1)**:
- Python + Pygame
- JSON data logging
- Manual feature engineering

**Planned (Phase 2+)**:
- PyTorch (LSTM + Transformer models)
- PostgreSQL + Pinecone/Weaviate (vector DB)
- FastAPI (integration API)
- Scikit-learn (hierarchical classifiers)

---

## 📁 Project Structure

```
/Prometheus
├── game.py              # Training game + data collection
├── requirements.txt     # Dependencies
├── README.md           # This file
├── CLAUDE.md           # AI assistant context
└── gameplay_data/      # Collected session data (gitignored)
```

---

## 🎯 Remember

**The current game is NOT the product** - it's a data collection tool and proof of concept.

**The real product** is the universal persistent player modeling framework that works across any combat game.

**Focus on**: Data quality, clear pattern separation, validated learning

**Avoid**: Over-engineering the game, adding unnecessary features, losing sight of the ML goal

---

*Building the future of personalized game AI, one session at a time.*
