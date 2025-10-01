# Playstyle Guide for Adaptive Combat AI

This guide explains the three distinct playstyles used for data collection and AI training. Understanding these playstyles is crucial for generating quality training data that will help the AI learn to adapt to different player behaviors.

---

## 🔴 AGGRESSIVE - Close Combat Rusher

### Definition
Aggressive players actively **pursue enemies**, engaging in close-range combat with high mobility and risk-taking behavior. They move **toward threats** to eliminate them quickly.

### Key Characteristics
- **Movement Direction**: Moving **toward** enemies (pursuit movement > 40%)
- **Combat Range**: Close quarters (< 120 pixels from enemies)
- **Positioning**: Constantly pushing forward, circling enemies
- **Kill Rate**: High kills per second (> 0.15)
- **Mobility**: High movement speed, dodging while advancing
- **Cover Usage**: Low - rarely stops to use cover
- **Damage Taken**: Higher damage taken due to exposure
- **Strategy**: Overwhelm enemies with speed and aggression

### How to Play Aggressively
1. **Always move toward the nearest enemy** - don't retreat
2. **Get close** - within 1-2 character lengths
3. **Circle and dodge** - strafe around enemies while shooting
4. **Keep moving** - never stand still, even when shooting
5. **Ignore cover** - prioritize offense over defense
6. **Push through damage** - accept taking hits to secure kills
7. **Fast-paced** - constant action, minimal downtime

### Typical Metrics
- Retreat Movement: < 20%
- Pursuit Movement: > 40%
- Average Enemy Distance: < 120 pixels
- Kill Rate: > 0.15 kills/second
- Shot Accuracy: 30-50% (shooting while moving)
- Mobility Index: > 150 px/sec

### Example Gameplay Loop
1. Enemy spawns → Run directly toward them
2. Get within close range → Start circling/strafing
3. Shoot while dodging → Eliminate enemy
4. Immediately pursue next target → Repeat

---

## 🔵 DEFENSIVE - Tactical Retreat Specialist

### Definition
Defensive players prioritize **survival and positioning**, using **tactical retreats** to maintain advantageous distance and cover. They move **away from threats** to create safe shooting positions.

### Key Characteristics
- **Movement Direction**: Moving **away** from enemies (retreat movement > 40%)
- **Combat Range**: Long range (> 180 pixels from enemies)
- **Positioning**: Behind cover, repositioning when threatened
- **Kill Rate**: Moderate to high, but from safe positions
- **Mobility**: Strategic movement - retreat when enemies close in
- **Cover Usage**: High - frequently behind obstacles
- **Damage Taken**: Low - prioritizes survival
- **Strategy**: Shoot from safe positions → Retreat when threatened → Re-engage

### How to Play Defensively
1. **Find cover immediately** when enemies spawn
2. **Maintain distance** - shoot from far range (3-4 character lengths)
3. **Tactical retreat** - when enemies get close, move to new cover
4. **Shoot from stationary positions** - stop to aim accurately
5. **Reposition often** - don't let enemies corner you
6. **Movement is retreat** - always moving AWAY from threats
7. **Patient playstyle** - wait for safe shots, don't rush

### Typical Metrics
- Retreat Movement: > 40%
- Pursuit Movement: < 20%
- Average Enemy Distance: > 180 pixels
- Kill Rate: 0.08-0.15 kills/second
- Shot Accuracy: > 40% (deliberate aimed shots)
- Survivability: < 0.8 damage/second
- Cover Usage: > 40%

### Example Gameplay Loop
1. Enemy spawns → Move to nearest cover
2. Peek out → Shoot from safe distance
3. Enemy approaches → Retreat to farther cover
4. Re-engage from new position → Eliminate enemy
5. Maintain distance throughout → Repeat

### Important Note
**High kill rate ≠ Aggressive if you're retreating!** You can be very effective (high accuracy, many kills) while still playing defensively. The key is **movement direction** - are you moving away from threats or toward them?

---

## 🟡 CHAOTIC - Unfocused/Panic Mode

### Definition
Chaotic players have **no clear strategy**, exhibiting erratic movement, poor accuracy, and inconsistent decision-making. They're neither effectively retreating nor pursuing - just reacting without a plan.

### Key Characteristics
- **Movement Direction**: **Neither** retreating nor pursuing consistently
- **Combat Range**: Medium distance (120-180 pixels)
- **Positioning**: Random, no pattern
- **Kill Rate**: Low with poor efficiency
- **Mobility**: Either too much (panicked running) or too little (frozen)
- **Cover Usage**: Inconsistent or ineffective
- **Damage Taken**: High due to poor positioning
- **Strategy**: No strategy - pure reaction

### How to Play Chaotically
1. **No planning** - react to each enemy individually
2. **Medium distance** - not committing to close or far
3. **Erratic movement** - running around without purpose
4. **Panic shooting** - spray bullets without aiming
5. **Inconsistent positioning** - sometimes hiding, sometimes rushing
6. **No retreat pattern** - move randomly when threatened
7. **Poor decision making** - reload at bad times, ignore threats

### Typical Metrics
- Retreat Movement: < 40%
- Pursuit Movement: < 40%
- Average Enemy Distance: 120-180 pixels (medium)
- Shot Accuracy: < 25%
- Damage Efficiency: < 0.8x (deal less than you take)
- Survivability: > 1.5 damage/second
- Movement: Either very high or very low, no consistency

### Example Gameplay Loop
1. Enemy spawns → Panic, unsure what to do
2. Shoot wildly while moving randomly
3. Take damage → Run in random direction
4. Reload at bad time → More panic
5. Eventually die or accidentally eliminate enemy → Repeat

---

## 📊 Understanding the Metrics

### Movement Direction (Most Important!)
- **Retreat %**: Percentage of time moving away from nearest enemy
- **Pursuit %**: Percentage of time moving toward nearest enemy
- **Neutral %**: Percentage of time moving sideways or stationary

**This is the PRIMARY differentiator** between playstyles:
- Aggressive = High Pursuit
- Defensive = High Retreat
- Chaotic = Low Both (no clear pattern)

### Other Key Metrics
- **Average Enemy Distance**: How far you maintain from enemies
- **Kill Rate**: Kills per second
- **Shot Accuracy**: Percentage of shots that hit
- **Damage Efficiency**: Damage dealt ÷ Damage taken
- **Mobility Index**: Pixels traveled per second
- **Cover Usage**: Percentage of time behind cover
- **Survivability**: Damage taken per second

---

## 🎯 Tips for Quality Data Collection

### For Aggressive Data
- ✅ Always chase enemies
- ✅ Get in their face
- ✅ Keep moving toward them
- ❌ Don't retreat even at low health
- ❌ Don't use cover
- ❌ Don't keep distance

### For Defensive Data
- ✅ Always retreat when enemies approach
- ✅ Use cover constantly
- ✅ Maintain long distance
- ❌ Don't chase enemies
- ❌ Don't fight at close range
- ❌ Don't stand in the open

### For Chaotic Data
- ✅ React without thinking
- ✅ Shoot while moving erratically
- ✅ Make bad decisions
- ❌ Don't have a consistent strategy
- ❌ Don't commit to any playstyle
- ❌ Don't optimize your gameplay

---

## 🔍 Why Movement Direction Matters

Previously, the AI couldn't distinguish between:
- A player moving backward while shooting (defensive retreat)
- A player moving forward while shooting (aggressive pursuit)

Both might have high mobility and kills, but the **intent** is completely different!

**Now the system tracks**:
- Vector from player to nearest enemy
- Player's movement velocity
- Dot product to determine direction
- Whether you're moving toward, away, or perpendicular to threats

This allows accurate classification of tactical retreat (defensive) vs aggressive rush.

---

## 📝 Data Collection Workflow

1. **Choose a playstyle** from the menu
2. **Commit to that playstyle** for the entire session
3. **Play 5-10 sessions** per playstyle (totaling 15-30 sessions)
4. **Check classification** after each session to verify accuracy
5. **Re-play if misclassified** - the metrics will tell you why

### What Makes Good Training Data
- **Consistency**: Same playstyle throughout the session
- **Variety**: Different sessions with same label should vary naturally
- **Extremes**: Play each style to its extreme (very aggressive, very defensive)
- **Completion**: Finish multiple waves per session for sufficient data
- **Intent**: Play the style you selected, even if it's not optimal

---

## ❓ Common Questions

**Q: Can I be defensive while getting lots of kills?**
A: Yes! High kill rate from long range while retreating = Defensive. It's about HOW you fight, not how much you kill.

**Q: If I'm behind cover shooting, isn't that defensive?**
A: Only if you're retreating to that cover. If you're pushing forward from cover to cover, that's aggressive positioning.

**Q: What if I naturally play a mix?**
A: For data collection, commit to ONE style per session. Real players mix styles, but the AI needs clear examples to learn from first.

**Q: How do I know if I played the right style?**
A: After the session, run the analyzer. Check "Movement Patterns" in the report:
- Aggressive should show high Pursuit % (>40%)
- Defensive should show high Retreat % (>40%)
- Chaotic should show both low (<40%)

---

## 🎮 Controls Reminder

- **WASD / Arrow Keys**: Move
- **Mouse**: Aim
- **Left Click**: Shoot
- **R**: Reload
- **ESC**: Quit and save data

---

## 📈 Next Steps After Data Collection

Once you have 5-10 sessions per playstyle:
1. Run `analyze_player_behavior.py --dir gameplay_data/<playstyle>`
2. Check classification accuracy in the aggregate report
3. If accuracy < 80%, adjust your playstyle or thresholds
4. Once accurate, use this data to train the ML model

---

**Remember**: The goal is to generate **clear, distinct training data** that teaches the AI to recognize and counter different playstyles. Play each style intentionally and consistently!
