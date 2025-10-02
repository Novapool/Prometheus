import json
from typing import Dict, List, Tuple
from datetime import datetime


class GameplayAnalyzer:
    """Analyzes gameplay data and classifies player behavior patterns."""

    # Classification thresholds
    THRESHOLDS = {
        'avg_enemy_distance': {
            'close': 150,      # < 150px = close combat (increased from 120)
            'medium': 250,     # 150-250px = medium range (was 180)
            'far': 250         # > 250px = long range
        },
        'cover_usage': {
            'none': 0.05,      # < 5% = no cover usage
            'low': 0.15,       # 5-15% = occasional cover
            'medium': 0.30,    # 15-30% = moderate cover usage
            'high': 0.30       # > 30% = heavy cover usage
        },
        'tactical_positioning': {  # NEW: Combined metric
            'low': 0.2,        # Not using tactical positions
            'medium': 0.4,     # Some tactical play
            'high': 0.4        # Strong tactical positioning
        },
        'shot_accuracy': {
            'poor': 0.30,      # < 30% accuracy (increased from 25%)
            'good': 0.45,      # 30-45% accuracy
            'excellent': 0.60  # > 60% accuracy (more selective)
        },
        'kill_rate': {  # Renamed from 'aggression'
            'low': 0.10,       # < 0.10 kills per second
            'medium': 0.20,    # 0.10-0.20 kills per second
            'high': 0.20       # > 0.20 kills per second
        },
        'damage_dealt': {
            'low': 100,        # < 100 damage
            'medium': 200,     # 100-200 damage
            'high': 200        # > 200 damage
        },
        'survivability_rate': {
            'excellent': 1.0,  # < 1.0 damage per second
            'good': 2.0,       # 1.0-2.0 damage per second
            'poor': 2.0        # > 2.0 damage per second
        },
        'mobility_index': {
            'very_low': 20,    # < 20 px/sec
            'low': 80,         # 20-80 px/sec
            'medium': 150,     # 80-150 px/sec
            'high': 150        # > 150 px/sec
        },
        'damage_efficiency': {
            'poor': 0.8,       # < 0.8x (more lenient)
            'good': 1.5,       # 0.8-1.5x
            'excellent': 1.5   # > 1.5x
        },
        'retreat_pct': {
            'low': 0.25,       # < 25% retreat movement
            'medium': 0.35,    # 25-35% retreat movement
            'high': 0.35       # > 35% retreat movement (tactical retreat)
        },
        'pursuit_pct': {
            'low': 0.25,       # < 25% pursuit movement
            'medium': 0.35,    # 25-35% pursuit movement
            'high': 0.35       # > 35% pursuit movement (aggressive)
        },
        'engagement_range': {  # NEW: How player chooses to engage
            'point_blank': 100,
            'close': 200,
            'medium': 300,
            'long': 300
        }
    }

    def __init__(self, json_filepath: str):
        """Initialize analyzer with gameplay data file."""
        self.filepath = json_filepath
        self.data = self._load_json()
        self._validate_data()
        self.features = {}
        self.classification = {}

    def _load_json(self) -> Dict:
        """Load gameplay data from JSON file."""
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find gameplay data file: {self.filepath}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {self.filepath}")

    def _validate_data(self) -> None:
        """Validate required fields exist in gameplay data."""
        required_fields = ['session_id', 'start_time', 'player_stats', 'events']
        required_stats = [
            'shots_fired', 'shots_hit', 'total_damage_dealt',
            'total_damage_taken', 'enemies_killed', 'distance_traveled'
        ]

        # Check top-level fields
        missing = [field for field in required_fields if field not in self.data]
        if missing:
            raise ValueError(f"Missing required fields in gameplay data: {missing}")

        # Check player_stats fields
        player_stats = self.data.get('player_stats', {})
        missing_stats = [stat for stat in required_stats if stat not in player_stats]
        if missing_stats:
            raise ValueError(f"Missing required player stats: {missing_stats}")

        # Validate events is a list
        if not isinstance(self.data.get('events'), list):
            raise ValueError("Field 'events' must be a list")

        # Validate behavioral_metrics is a list (if present)
        behavioral_metrics = self.data.get('behavioral_metrics')
        if behavioral_metrics is not None and not isinstance(behavioral_metrics, list):
            raise ValueError("Field 'behavioral_metrics' must be a list")

    def extract_features(self) -> Dict:
        """Extract all behavioral features from raw gameplay data."""
        self.features = {
            **self._extract_combat_metrics(),
            **self._extract_spatial_metrics(),
            **self._extract_temporal_metrics(),
            **self._extract_risk_metrics()
        }

        # Add enhanced tactical metrics
        self.features.update(self._extract_tactical_metrics())

        return self.features

    def _extract_combat_metrics(self) -> Dict:
        """Calculate combat-related metrics."""
        stats = self.data['player_stats']

        shots_fired = stats['shots_fired']
        shots_hit = stats['shots_hit']

        # Avoid division by zero
        shot_accuracy = shots_hit / shots_fired if shots_fired > 0 else 0
        damage_per_shot = stats['total_damage_dealt'] / shots_fired if shots_fired > 0 else 0

        # Calculate engagement efficiency (kills per engagement)
        engagement_efficiency = stats['enemies_killed'] / shots_fired if shots_fired > 0 else 0

        return {
            'shot_accuracy': shot_accuracy,
            'damage_per_shot': damage_per_shot,
            'total_damage_dealt': stats['total_damage_dealt'],
            'total_damage_taken': stats['total_damage_taken'],
            'enemies_killed': stats['enemies_killed'],
            'shots_fired': shots_fired,
            'shots_hit': shots_hit,
            'engagement_efficiency': engagement_efficiency
        }

    def _extract_spatial_metrics(self) -> Dict:
        """Enhanced spatial metrics with better cover detection."""
        behavioral_data = self.data.get('behavioral_metrics', [])

        if not behavioral_data:
            return {
                'avg_enemy_distance': 0,
                'cover_usage_pct': 0,
                'near_cover_pct': 0,
                'effective_cover_usage': 0,
                'mobility_index': 0,
                'distance_traveled': 0,
                'retreat_pct': 0,
                'pursuit_pct': 0,
                'neutral_pct': 0
            }

        # Filter out invalid distance measurements (when no enemies present)
        valid_distances = []
        cover_frames = 0
        near_cover_frames = 0

        for frame in behavioral_data:
            # Only count distance when enemies are actually present
            if frame.get('enemies_count', 0) > 0 and frame.get('avg_enemy_distance', 0) > 0:
                # Cap distance at reasonable screen bounds
                dist = min(frame['avg_enemy_distance'], 500)  # Max reasonable distance
                valid_distances.append(dist)

            # Count cover usage (both near and using)
            if frame.get('using_cover', False):
                cover_frames += 1
            if frame.get('near_cover', False):
                near_cover_frames += 1

        # Calculate averages
        avg_distance = sum(valid_distances) / len(valid_distances) if valid_distances else 0

        # Enhanced cover usage calculation
        # Consider both "using cover" and "near cover" with different weights
        cover_usage_pct = cover_frames / len(behavioral_data) if behavioral_data else 0
        near_cover_pct = near_cover_frames / len(behavioral_data) if behavioral_data else 0

        # Combined cover score (being behind cover is worth more than just being near)
        effective_cover_usage = (cover_usage_pct * 1.0) + (near_cover_pct * 0.3)
        effective_cover_usage = min(effective_cover_usage, 1.0)  # Cap at 100%

        # Movement metrics
        stats = self.data['player_stats']
        distance_traveled = stats['distance_traveled']
        session_duration = self._calculate_session_duration()
        mobility_index = distance_traveled / session_duration if session_duration > 0 else 0

        # Movement direction percentages
        total_frames = stats.get('retreat_frames', 0) + stats.get('pursuit_frames', 0) + stats.get('neutral_frames', 0)

        retreat_pct = stats.get('retreat_frames', 0) / total_frames if total_frames > 0 else 0
        pursuit_pct = stats.get('pursuit_frames', 0) / total_frames if total_frames > 0 else 0
        neutral_pct = stats.get('neutral_frames', 0) / total_frames if total_frames > 0 else 0

        return {
            'avg_enemy_distance': avg_distance,
            'cover_usage_pct': cover_usage_pct,
            'near_cover_pct': near_cover_pct,
            'effective_cover_usage': effective_cover_usage,
            'mobility_index': mobility_index,
            'distance_traveled': distance_traveled,
            'retreat_pct': retreat_pct,
            'pursuit_pct': pursuit_pct,
            'neutral_pct': neutral_pct
        }

    def _extract_temporal_metrics(self) -> Dict:
        """Calculate time-based metrics."""
        session_duration = self._calculate_session_duration()

        # Calculate rates (per second)
        kill_rate = (self.data['player_stats']['enemies_killed'] /
                    session_duration if session_duration > 0 else 0)
        shot_frequency = (self.data['player_stats']['shots_fired'] /
                         session_duration if session_duration > 0 else 0)

        return {
            'session_duration': session_duration,
            'kill_rate': kill_rate,
            'shot_frequency': shot_frequency
        }

    def _extract_risk_metrics(self) -> Dict:
        """Calculate risk-taking behavior metrics."""
        session_duration = self._calculate_session_duration()

        # Survivability: lower is better
        survivability = (self.data['player_stats']['total_damage_taken'] /
                        session_duration if session_duration > 0 else 0)

        # Damage efficiency: higher is better
        damage_taken = max(self.data['player_stats']['total_damage_taken'], 1)
        damage_efficiency = self.data['player_stats']['total_damage_dealt'] / damage_taken

        return {
            'survivability': survivability,
            'damage_efficiency': damage_efficiency
        }

    def _extract_tactical_metrics(self) -> Dict:
        """NEW: Extract tactical positioning and engagement patterns."""
        import math

        behavioral_data = self.data.get('behavioral_metrics', [])
        events = self.data.get('events', [])

        if not behavioral_data:
            return {
                'tactical_positioning_score': 0,
                'engagement_range_preference': 'unknown',
                'defensive_action_ratio': 0
            }

        # Analyze engagement ranges from shot events
        shot_distances = []
        for event in events:
            if event.get('type') == 'shot_fired' and event.get('data'):
                data = event['data']
                if 'position' in data and 'target_position' in data:
                    pos = data['position']
                    target = data['target_position']
                    dist = math.sqrt((target[0] - pos[0])**2 + (target[1] - pos[1])**2)
                    shot_distances.append(dist)

        # Determine preferred engagement range
        if shot_distances:
            avg_shot_dist = sum(shot_distances) / len(shot_distances)
            if avg_shot_dist < self.THRESHOLDS['engagement_range']['point_blank']:
                engagement_pref = 'point_blank'
            elif avg_shot_dist < self.THRESHOLDS['engagement_range']['close']:
                engagement_pref = 'close'
            elif avg_shot_dist < self.THRESHOLDS['engagement_range']['medium']:
                engagement_pref = 'medium'
            else:
                engagement_pref = 'long'
        else:
            engagement_pref = 'unknown'

        # Calculate tactical positioning score
        # Combines: cover usage, good positioning (distance), low damage taken
        tactical_score = 0

        # Factor 1: Cover usage (40% weight)
        if self.features.get('effective_cover_usage', 0) > self.THRESHOLDS['cover_usage']['medium']:
            tactical_score += 0.4
        elif self.features.get('effective_cover_usage', 0) > self.THRESHOLDS['cover_usage']['low']:
            tactical_score += 0.2

        # Factor 2: Maintaining optimal distance (30% weight)
        avg_dist = self.features.get('avg_enemy_distance', 0)
        if 150 < avg_dist < 300:  # Optimal tactical range
            tactical_score += 0.3
        elif avg_dist > 300:  # Long range
            tactical_score += 0.2

        # Factor 3: Low damage taken (30% weight)
        if self.features.get('survivability', 999) < self.THRESHOLDS['survivability_rate']['excellent']:
            tactical_score += 0.3
        elif self.features.get('survivability', 999) < self.THRESHOLDS['survivability_rate']['good']:
            tactical_score += 0.15

        # Calculate defensive action ratio (reloads and retreats during combat)
        reload_events = len([e for e in events if e.get('type') == 'reload_start'])
        total_combat_events = len([e for e in events if e.get('type') in ['shot_fired', 'reload_start']])
        defensive_action_ratio = reload_events / total_combat_events if total_combat_events > 0 else 0

        return {
            'tactical_positioning_score': tactical_score,
            'engagement_range_preference': engagement_pref,
            'defensive_action_ratio': defensive_action_ratio
        }

    def _calculate_session_duration(self) -> float:
        """Calculate total session duration in seconds."""
        events = self.data.get('events', [])
        if not events:
            return 0.1  # Minimum duration to avoid division by zero

        start_time = self.data['start_time']
        end_time = events[-1]['timestamp']
        duration = end_time - start_time

        if duration < 0:
            raise ValueError(f"Invalid session: end_time ({end_time}) < start_time ({start_time})")

        # Return minimum duration to avoid division by zero
        return max(duration, 0.1)

    def classify_behavior(self) -> Dict:
        """Classify player behavior based on extracted features."""
        if not self.features:
            self.extract_features()

        # Calculate scores for each behavior type
        scores = {
            'aggressive': self._calculate_aggressive_score(),
            'defensive': self._calculate_defensive_score(),
            'chaotic': self._calculate_chaotic_score()
        }

        # Normalize scores to sum to 1
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}

        # Determine primary and secondary classifications
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_scores[0]
        secondary = sorted_scores[1]

        self.classification = {
            'primary': primary[0],
            'primary_confidence': primary[1],
            'secondary': secondary[0],
            'secondary_confidence': secondary[1],
            'all_scores': scores
        }

        return self.classification

    def _calculate_aggressive_score(self) -> float:
        """Enhanced aggressive scoring.

        Aggressive = pursues enemies, close-range combat, high mobility, rushes in.
        """
        score = 0.0

        # Primary indicators (60% total weight)
        # 1. Pursuit movement (30%)
        if self.features.get('pursuit_pct', 0) > self.THRESHOLDS['pursuit_pct']['high']:
            score += 0.30
        elif self.features.get('pursuit_pct', 0) > self.THRESHOLDS['pursuit_pct']['medium']:
            score += 0.20
        elif self.features.get('pursuit_pct', 0) > self.THRESHOLDS['pursuit_pct']['low']:
            score += 0.10

        # 2. Close combat preference (30%)
        if self.features.get('avg_enemy_distance', 999) < self.THRESHOLDS['avg_enemy_distance']['close']:
            score += 0.30
        elif self.features.get('engagement_range_preference') == 'close':
            score += 0.20
        elif self.features.get('engagement_range_preference') == 'point_blank':
            score += 0.25

        # Secondary indicators (40% total weight)
        # 3. High kill rate (15%)
        if self.features.get('kill_rate', 0) > self.THRESHOLDS['kill_rate']['high']:
            score += 0.15
        elif self.features.get('kill_rate', 0) > self.THRESHOLDS['kill_rate']['medium']:
            score += 0.08

        # 4. Low cover usage (10%)
        if self.features.get('effective_cover_usage', 1) < self.THRESHOLDS['cover_usage']['low']:
            score += 0.10
        elif self.features.get('effective_cover_usage', 1) < self.THRESHOLDS['cover_usage']['medium']:
            score += 0.05

        # 5. High mobility (10%)
        if self.features.get('mobility_index', 0) > 150:
            score += 0.10
        elif self.features.get('mobility_index', 0) > 100:
            score += 0.05

        # 6. Low tactical positioning (5%)
        if self.features.get('tactical_positioning_score', 1) < self.THRESHOLDS['tactical_positioning']['low']:
            score += 0.05

        return min(score, 1.0)

    def _calculate_defensive_score(self) -> float:
        """Enhanced defensive scoring with proper cover and tactical weighting.

        Defensive = tactical retreat, maintains distance, uses cover, prioritizes survival.
        Movement is AWAY from enemies to reposition, not toward them.
        """
        score = 0.0

        # Primary indicators (70% total weight)
        # 1. Tactical positioning (25%) - NEW PRIMARY INDICATOR
        if self.features.get('tactical_positioning_score', 0) > self.THRESHOLDS['tactical_positioning']['high']:
            score += 0.25
        elif self.features.get('tactical_positioning_score', 0) > self.THRESHOLDS['tactical_positioning']['medium']:
            score += 0.15
        elif self.features.get('tactical_positioning_score', 0) > self.THRESHOLDS['tactical_positioning']['low']:
            score += 0.08

        # 2. Retreat movement (20%)
        if self.features.get('retreat_pct', 0) > self.THRESHOLDS['retreat_pct']['high']:
            score += 0.20
        elif self.features.get('retreat_pct', 0) > self.THRESHOLDS['retreat_pct']['medium']:
            score += 0.12
        elif self.features.get('retreat_pct', 0) > self.THRESHOLDS['retreat_pct']['low']:
            score += 0.06

        # 3. Distance maintenance (15%)
        if self.features.get('avg_enemy_distance', 0) > self.THRESHOLDS['avg_enemy_distance']['far']:
            score += 0.15
        elif self.features.get('avg_enemy_distance', 0) > self.THRESHOLDS['avg_enemy_distance']['medium']:
            score += 0.10
        elif self.features.get('engagement_range_preference') in ['long', 'medium']:
            score += 0.08

        # 4. Cover usage (10%)
        if self.features.get('effective_cover_usage', 0) > self.THRESHOLDS['cover_usage']['high']:
            score += 0.10
        elif self.features.get('effective_cover_usage', 0) > self.THRESHOLDS['cover_usage']['medium']:
            score += 0.07
        elif self.features.get('effective_cover_usage', 0) > self.THRESHOLDS['cover_usage']['low']:
            score += 0.04

        # Secondary indicators (30% total weight)
        # 5. Good survivability (10%)
        if self.features.get('survivability', 999) < self.THRESHOLDS['survivability_rate']['excellent']:
            score += 0.10
        elif self.features.get('survivability', 999) < self.THRESHOLDS['survivability_rate']['good']:
            score += 0.05

        # 6. High accuracy (10%) - Patient, aimed shots
        if self.features.get('shot_accuracy', 0) > self.THRESHOLDS['shot_accuracy']['excellent']:
            score += 0.10
        elif self.features.get('shot_accuracy', 0) > self.THRESHOLDS['shot_accuracy']['good']:
            score += 0.06

        # 7. Good damage efficiency (5%)
        if self.features.get('damage_efficiency', 0) > 2.0:
            score += 0.05
        elif self.features.get('damage_efficiency', 0) > 1.5:
            score += 0.03

        # 8. Defensive actions (5%)
        if self.features.get('defensive_action_ratio', 0) > 0.1:
            score += 0.05
        elif self.features.get('defensive_action_ratio', 0) > 0.05:
            score += 0.02

        return min(score, 1.0)


    def _calculate_chaotic_score(self) -> float:
        """Enhanced chaotic scoring.

        Chaotic = no clear strategy, inconsistent movement, poor accuracy, medium range,
        neither retreating strategically nor pursuing aggressively.
        """
        score = 0.0

        # Primary indicators (60% total weight)
        # 1. Poor accuracy (20%)
        if self.features.get('shot_accuracy', 1) < self.THRESHOLDS['shot_accuracy']['poor']:
            score += 0.20
        elif self.features.get('shot_accuracy', 1) < self.THRESHOLDS['shot_accuracy']['good']:
            score += 0.10

        # 2. Poor survivability (20%)
        if self.features.get('survivability', 0) > self.THRESHOLDS['survivability_rate']['poor']:
            score += 0.20
        elif self.features.get('survivability', 0) > self.THRESHOLDS['survivability_rate']['good']:
            score += 0.10

        # 3. No clear movement pattern (20%)
        retreat = self.features.get('retreat_pct', 0)
        pursuit = self.features.get('pursuit_pct', 0)
        if retreat < self.THRESHOLDS['retreat_pct']['medium'] and pursuit < self.THRESHOLDS['pursuit_pct']['medium']:
            score += 0.20
        elif retreat < self.THRESHOLDS['retreat_pct']['high'] and pursuit < self.THRESHOLDS['pursuit_pct']['high']:
            score += 0.10

        # Secondary indicators (40% total weight)
        # 4. Poor damage efficiency (15%)
        if self.features.get('damage_efficiency', 999) < 1.0:
            score += 0.15
        elif self.features.get('damage_efficiency', 999) < 1.5:
            score += 0.08

        # 5. Low kill rate (10%)
        if self.features.get('kill_rate', 1) < self.THRESHOLDS['kill_rate']['low']:
            score += 0.10
        elif self.features.get('kill_rate', 1) < self.THRESHOLDS['kill_rate']['medium']:
            score += 0.05

        # 6. Inconsistent positioning (10%)
        # Medium distance, low tactical score
        if (self.features.get('avg_enemy_distance', 0) > self.THRESHOLDS['avg_enemy_distance']['close'] and
            self.features.get('avg_enemy_distance', 0) < self.THRESHOLDS['avg_enemy_distance']['far']):
            score += 0.05

        if self.features.get('tactical_positioning_score', 1) < self.THRESHOLDS['tactical_positioning']['medium']:
            score += 0.05

        # 7. Erratic engagement (5%)
        if self.features.get('engagement_range_preference') == 'unknown':
            score += 0.05

        return min(score, 1.0)

    def generate_adaptations(self) -> Dict:
        """Generate enemy behavior adaptation recommendations."""
        if not self.classification:
            self.classify_behavior()

        primary_style = self.classification['primary']

        adaptation_map = {
            'aggressive': {
                'strategy': 'Counter aggressive rushers with defensive tactics',
                'recommendations': [
                    'Increase enemy spawn distance from player',
                    'Deploy more ranged/sniper-type enemies',
                    'Enemies should maintain distance and kite',
                    'Use cover more effectively',
                    'Implement retreat behavior when player gets close'
                ],
                'enemy_type_ratio': {'basic': 0.3, 'sniper': 0.7},
                'difficulty_modifier': 1.2  # Increase difficulty
            },
            'defensive': {
                'strategy': 'Force defensive players out of comfort zone',
                'recommendations': [
                    'Increase pressure with more aggressive enemies',
                    'Deploy rushing enemy types',
                    'Use flanking maneuvers',
                    'Flush player out of cover with area attacks',
                    'Reduce enemy spawn distance'
                ],
                'enemy_type_ratio': {'basic': 0.8, 'sniper': 0.2},
                'difficulty_modifier': 1.1
            },
            'chaotic': {
                'strategy': 'Provide more structured challenge to build skills',
                'recommendations': [
                    'Reduce enemy count slightly',
                    'Use more predictable enemy patterns',
                    'Give player more time to react',
                    'Increase ammo drops',
                    'Balance enemy types evenly'
                ],
                'enemy_type_ratio': {'basic': 0.5, 'sniper': 0.5},
                'difficulty_modifier': 0.9  # Reduce difficulty
            }
        }

        return adaptation_map.get(primary_style, adaptation_map['defensive'])

    def generate_report(self) -> str:
        """Generate human-readable analysis report."""
        if not self.features:
            self.extract_features()
        if not self.classification:
            self.classify_behavior()

        adaptations = self.generate_adaptations()

        report = f"""
{'='*70}
PLAYER BEHAVIOR ANALYSIS REPORT
{'='*70}

Session ID: {self.data['session_id']}
Duration: {self.features['session_duration']:.1f} seconds
Date: {datetime.fromtimestamp(self.data['start_time']).strftime('%Y-%m-%d %H:%M:%S')}

{'='*70}
CLASSIFICATION
{'='*70}

Primary Style:    {self.classification['primary'].upper()}
Confidence:       {self.classification['primary_confidence']*100:.1f}%

Secondary Trait:  {self.classification['secondary'].upper()}
Confidence:       {self.classification['secondary_confidence']*100:.1f}%

All Scores:
  - Aggressive: {self.classification['all_scores']['aggressive']*100:.1f}%
  - Defensive:  {self.classification['all_scores']['defensive']*100:.1f}%
  - Chaotic:    {self.classification['all_scores']['chaotic']*100:.1f}%

{'='*70}
KEY METRICS
{'='*70}

Combat Performance:
  - Shot Accuracy:        {self.features['shot_accuracy']*100:.1f}%
  - Enemies Killed:       {self.features['enemies_killed']}
  - Damage Dealt:         {self.features['total_damage_dealt']:.0f}
  - Damage Taken:         {self.features['total_damage_taken']:.0f}
  - Damage Efficiency:    {self.features['damage_efficiency']:.2f}x
  - Engagement Efficiency: {self.features.get('engagement_efficiency', 0):.3f} (kills/shot)

Spatial Behavior:
  - Avg Enemy Distance:   {self.features['avg_enemy_distance']:.1f} pixels
  - Cover Usage:          {self.features['cover_usage_pct']*100:.1f}%
  - Effective Cover Usage: {self.features.get('effective_cover_usage', 0)*100:.1f}%
  - Distance Traveled:    {self.features['distance_traveled']:.1f} pixels
  - Mobility Index:       {self.features['mobility_index']:.1f} px/sec

Movement Patterns:
  - Retreat Movement:     {self.features.get('retreat_pct', 0)*100:.1f}% (moving away from enemies)
  - Pursuit Movement:     {self.features.get('pursuit_pct', 0)*100:.1f}% (moving toward enemies)
  - Neutral Movement:     {self.features.get('neutral_pct', 0)*100:.1f}% (sideways/stationary)

Tactical Metrics:
  - Tactical Positioning:  {self.features.get('tactical_positioning_score', 0)*100:.1f}%
  - Engagement Range:      {self.features.get('engagement_range_preference', 'unknown')}
  - Defensive Actions:     {self.features.get('defensive_action_ratio', 0)*100:.1f}%

Aggression Metrics:
  - Kill Rate:            {self.features.get('kill_rate', 0):.3f} kills/sec
  - Shots per Second:     {self.features['shot_frequency']:.2f}
  - Survivability:        {self.features['survivability']:.2f} dmg/sec

{'='*70}
RECOMMENDED ENEMY ADAPTATIONS
{'='*70}

Strategy: {adaptations['strategy']}

Specific Recommendations:
"""
        for i, rec in enumerate(adaptations['recommendations'], 1):
            report += f"  {i}. {rec}\n"

        report += f"""
Enemy Type Ratio:
  - Basic (Aggressive): {adaptations['enemy_type_ratio']['basic']*100:.0f}%
  - Sniper (Ranged):    {adaptations['enemy_type_ratio']['sniper']*100:.0f}%

Difficulty Modifier: {adaptations['difficulty_modifier']}x

{'='*70}
"""
        return report

    def save_classification(self, output_filepath: str = None, output_dir: str = None):
        """Save classification results to JSON file.

        Args:
            output_filepath: Full path to output file (optional)
            output_dir: Directory to save to, will auto-generate filename (optional)
        """
        import os

        if not self.classification:
            self.classify_behavior()

        adaptations = self.generate_adaptations()

        output_data = {
            'session_id': self.data['session_id'],
            'playstyle_label': self.data.get('playstyle_label'),
            'analysis_timestamp': datetime.now().isoformat(),
            'classification': self.classification,
            'features': self.features,
            'adaptations': adaptations
        }

        # Determine output path
        if output_filepath:
            final_path = output_filepath
        elif output_dir:
            # Auto-generate filename based on playstyle
            playstyle = self.data.get('playstyle_label', 'unknown')
            playstyle_dir = os.path.join(output_dir, playstyle)
            os.makedirs(playstyle_dir, exist_ok=True)
            final_path = os.path.join(playstyle_dir, f"analysis_{self.data['session_id']}.json")
        else:
            # Default fallback
            final_path = f"analysis_{self.data['session_id']}.json"

        with open(final_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"Classification saved to {final_path}")


def analyze_directory(directory_path: str):
    """Analyze all gameplay JSON files in a directory."""
    import os
    import glob

    # Find all JSON files in directory
    pattern = os.path.join(directory_path, "gameplay_data_*.json")
    json_files = glob.glob(pattern)

    if not json_files:
        print(f"No gameplay data files found in {directory_path}")
        return

    print(f"\nFound {len(json_files)} gameplay data files")
    print("="*70)

    results = []
    correct_classifications = 0
    total_labeled = 0

    # Extract expected playstyle from directory path
    expected_playstyle = os.path.basename(directory_path)

    # Output goes to analysis_results/
    output_base_dir = "analysis_results"
    os.makedirs(output_base_dir, exist_ok=True)

    for filepath in json_files:
        try:
            print(f"\nAnalyzing: {os.path.basename(filepath)}")

            # Analyze file
            analyzer = GameplayAnalyzer(filepath)
            analyzer.extract_features()
            analyzer.classify_behavior()

            # Save individual analysis (will auto-organize by playstyle)
            analyzer.save_classification(output_dir=output_base_dir)

            # Track results
            label = analyzer.data.get('playstyle_label')
            predicted = analyzer.classification['primary']
            confidence = analyzer.classification['primary_confidence']

            result = {
                'filename': os.path.basename(filepath),
                'session_id': analyzer.data['session_id'],
                'label': label,
                'predicted': predicted,
                'confidence': confidence,
                'correct': label == predicted if label else None
            }
            results.append(result)

            # Count accuracy
            if label:
                total_labeled += 1
                if label == predicted:
                    correct_classifications += 1

            print(f"  Label: {label or 'none'} | Predicted: {predicted} ({confidence*100:.1f}%)")

        except Exception as e:
            print(f"  Error: {e}")
            continue

    # Generate aggregate report
    print("\n" + "="*70)
    print("AGGREGATE ANALYSIS REPORT")
    print("="*70)

    if total_labeled > 0:
        accuracy = correct_classifications / total_labeled
        print(f"\nLabel Validation:")
        print(f"  Expected Playstyle: {expected_playstyle}")
        print(f"  Total Sessions: {len(results)}")
        print(f"  Labeled Sessions: {total_labeled}")
        print(f"  Correct Classifications: {correct_classifications}")
        print(f"  Accuracy: {accuracy*100:.1f}%")
    else:
        print(f"\nNo labeled data found for validation")
        print(f"Total Sessions Analyzed: {len(results)}")

    # Classification distribution
    print(f"\nClassification Distribution:")
    from collections import Counter
    predictions = [r['predicted'] for r in results]
    distribution = Counter(predictions)
    for style, count in distribution.most_common():
        pct = count / len(results) * 100
        print(f"  {style}: {count} ({pct:.1f}%)")

    # Save aggregate report in the expected playstyle directory
    aggregate_dir = os.path.join(output_base_dir, expected_playstyle)
    os.makedirs(aggregate_dir, exist_ok=True)
    aggregate_file = os.path.join(aggregate_dir, "aggregate_report.txt")

    with open(aggregate_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("AGGREGATE ANALYSIS REPORT\n")
        f.write("="*70 + "\n\n")
        f.write(f"Directory: {directory_path}\n")
        f.write(f"Expected Playstyle: {expected_playstyle}\n")
        f.write(f"Total Sessions: {len(results)}\n")

        if total_labeled > 0:
            f.write(f"\nLabel Validation:\n")
            f.write(f"  Labeled Sessions: {total_labeled}\n")
            f.write(f"  Correct Classifications: {correct_classifications}\n")
            f.write(f"  Accuracy: {accuracy*100:.1f}%\n")

        f.write(f"\nClassification Distribution:\n")
        for style, count in distribution.most_common():
            pct = count / len(results) * 100
            f.write(f"  {style}: {count} ({pct:.1f}%)\n")

        f.write("\nIndividual Results:\n")
        for r in results:
            status = "✓" if r['correct'] else "✗" if r['correct'] is not None else "-"
            f.write(f"  {status} {r['filename']}: {r['label'] or 'unlabeled'} → {r['predicted']} ({r['confidence']*100:.1f}%)\n")

    print(f"\nAggregate report saved to {aggregate_file}")


def analyze_all_data(base_dir: str = "gameplay_data"):
    """Analyze all gameplay data from all playstyle subdirectories."""
    import os
    from collections import Counter

    # Find all subdirectories in base_dir
    if not os.path.isdir(base_dir):
        print(f"Error: {base_dir} is not a valid directory")
        return

    subdirs = [d for d in os.listdir(base_dir)
               if os.path.isdir(os.path.join(base_dir, d))]

    if not subdirs:
        print(f"No subdirectories found in {base_dir}")
        return

    print(f"\nProcessing all data from {base_dir}/")
    print(f"Found playstyle directories: {', '.join(subdirs)}")
    print("="*70)

    all_results = []

    # Process each subdirectory
    for subdir in sorted(subdirs):
        subdir_path = os.path.join(base_dir, subdir)
        print(f"\n{'='*70}")
        print(f"Processing {subdir_path}")
        print(f"{'='*70}")

        # Analyze this directory
        analyze_directory(subdir_path)

    print(f"\n{'='*70}")
    print("ALL DATA PROCESSED SUCCESSFULLY")
    print(f"{'='*70}")
    print(f"\nResults organized in analysis_results/ by playstyle")
    print(f"Each playstyle directory contains:")
    print(f"  - Individual analysis JSON files")
    print(f"  - aggregate_report.txt")


def main():
    """Main entry point for standalone usage."""
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file:  python analyze_player_behavior.py <gameplay_data.json>")
        print("  Directory:    python analyze_player_behavior.py --dir <directory_path>")
        print("  All data:     python analyze_player_behavior.py --all [base_directory]")
        print("\nExamples:")
        print("  python analyze_player_behavior.py gameplay_data_20250922_154913.json")
        print("  python analyze_player_behavior.py --dir gameplay_data/defensive")
        print("  python analyze_player_behavior.py --all")
        print("  python analyze_player_behavior.py --all gameplay_data")
        sys.exit(1)

    # Check for --all mode
    if sys.argv[1] == "--all":
        base_dir = sys.argv[2] if len(sys.argv) > 2 else "gameplay_data"
        try:
            analyze_all_data(base_dir)
        except Exception as e:
            print(f"Error analyzing all data: {e}")
            sys.exit(1)

    # Check for directory mode
    elif sys.argv[1] == "--dir":
        if len(sys.argv) < 3:
            print("Error: --dir requires a directory path")
            sys.exit(1)
        directory_path = sys.argv[2]

        if not os.path.isdir(directory_path):
            print(f"Error: {directory_path} is not a valid directory")
            sys.exit(1)

        try:
            analyze_directory(directory_path)
        except Exception as e:
            print(f"Error analyzing directory: {e}")
            sys.exit(1)
    else:
        # Single file mode
        input_file = sys.argv[1]

        try:
            # Create analyzer
            analyzer = GameplayAnalyzer(input_file)

            # Perform analysis
            analyzer.extract_features()
            analyzer.classify_behavior()

            # Generate and print report
            report = analyzer.generate_report()
            print(report)

            # Save classification to file (auto-organize by playstyle)
            analyzer.save_classification(output_dir="analysis_results")

        except Exception as e:
            print(f"Error analyzing gameplay data: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()