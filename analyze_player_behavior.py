import json
from typing import Dict, List, Tuple
from datetime import datetime


class GameplayAnalyzer:
    """Analyzes gameplay data and classifies player behavior patterns."""

    # Classification thresholds
    THRESHOLDS = {
        'avg_enemy_distance': {
            'close': 120,      # < 120px = close combat
            'medium': 180,     # 120-180px = medium range
            'far': 180         # > 180px = long range
        },
        'cover_usage': {
            'low': 0.2,        # < 20% = rarely uses cover
            'medium': 0.4,     # 20-40% = moderate cover usage
            'high': 0.5        # > 50% = heavy cover usage (more lenient)
        },
        'shot_accuracy': {
            'poor': 0.25,      # < 25% accuracy
            'good': 0.4,       # 25-40% accuracy
            'excellent': 0.5   # > 50% accuracy
        },
        'aggression': {
            'low': 0.08,       # < 0.08 kills per second
            'medium': 0.15,    # 0.08-0.15 kills per second
            'high': 0.15       # > 0.15 kills per second
        },
        'damage_dealt': {
            'low': 100,        # < 100 damage
            'medium': 200,     # 100-200 damage
            'high': 200        # > 200 damage
        },
        'survivability_rate': {
            'excellent': 0.8,  # < 0.8 damage per second (more lenient)
            'good': 1.5,       # 0.8-1.5 damage per second
            'poor': 1.5        # > 1.5 damage per second
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
            'low': 0.2,        # < 20% retreat movement
            'medium': 0.4,     # 20-40% retreat movement
            'high': 0.4        # > 40% retreat movement (tactical retreat)
        },
        'pursuit_pct': {
            'low': 0.2,        # < 20% pursuit movement
            'medium': 0.4,     # 20-40% pursuit movement
            'high': 0.4        # > 40% pursuit movement (aggressive)
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
        return self.features

    def _extract_combat_metrics(self) -> Dict:
        """Calculate combat-related metrics."""
        stats = self.data['player_stats']

        shots_fired = stats['shots_fired']
        shots_hit = stats['shots_hit']

        # Avoid division by zero
        shot_accuracy = shots_hit / shots_fired if shots_fired > 0 else 0
        damage_per_shot = stats['total_damage_dealt'] / shots_fired if shots_fired > 0 else 0

        return {
            'shot_accuracy': shot_accuracy,
            'damage_per_shot': damage_per_shot,
            'total_damage_dealt': stats['total_damage_dealt'],
            'total_damage_taken': stats['total_damage_taken'],
            'enemies_killed': stats['enemies_killed'],
            'shots_fired': shots_fired,
            'shots_hit': shots_hit
        }

    def _extract_spatial_metrics(self) -> Dict:
        """Calculate spatial behavior metrics."""
        behavioral_data = self.data.get('behavioral_metrics', [])

        if not behavioral_data:
            return {
                'avg_enemy_distance': 0,
                'cover_usage_pct': 0,
                'mobility_index': 0,
                'retreat_pct': 0,
                'pursuit_pct': 0
            }

        # Calculate average enemy distance across all sampled frames
        distances = [frame['avg_enemy_distance'] for frame in behavioral_data
                    if frame['avg_enemy_distance'] > 0]
        avg_distance = sum(distances) / len(distances) if distances else 0

        # Calculate cover usage percentage
        near_cover_frames = sum(1 for frame in behavioral_data if frame['near_cover'])
        cover_usage_pct = near_cover_frames / len(behavioral_data) if behavioral_data else 0

        # Calculate mobility
        distance_traveled = self.data['player_stats']['distance_traveled']
        session_duration = self._calculate_session_duration()
        mobility_index = distance_traveled / session_duration if session_duration > 0 else 0

        # Calculate retreat and pursuit percentages
        stats = self.data['player_stats']
        total_movement_frames = stats.get('retreat_frames', 0) + stats.get('pursuit_frames', 0) + stats.get('neutral_frames', 0)

        if total_movement_frames > 0:
            retreat_pct = stats.get('retreat_frames', 0) / total_movement_frames
            pursuit_pct = stats.get('pursuit_frames', 0) / total_movement_frames
        else:
            retreat_pct = 0
            pursuit_pct = 0

        return {
            'avg_enemy_distance': avg_distance,
            'cover_usage_pct': cover_usage_pct,
            'mobility_index': mobility_index,
            'distance_traveled': distance_traveled,
            'retreat_pct': retreat_pct,
            'pursuit_pct': pursuit_pct
        }

    def _extract_temporal_metrics(self) -> Dict:
        """Calculate time-based metrics."""
        session_duration = self._calculate_session_duration()

        # Calculate rates (per second)
        aggression_score = (self.data['player_stats']['enemies_killed'] /
                          session_duration if session_duration > 0 else 0)
        shot_frequency = (self.data['player_stats']['shots_fired'] /
                         session_duration if session_duration > 0 else 0)

        return {
            'session_duration': session_duration,
            'aggression_score': aggression_score,
            'shot_frequency': shot_frequency
        }

    def _extract_risk_metrics(self) -> Dict:
        """Calculate risk-taking behavior metrics."""
        session_duration = self._calculate_session_duration()

        # Survivability: lower is better
        survivability = (self.data['player_stats']['total_damage_taken'] /
                        session_duration if session_duration > 0 else 0)

        # Damage efficiency: higher is better
        damage_efficiency = (self.data['player_stats']['total_damage_dealt'] /
                           (self.data['player_stats']['total_damage_taken'] + 1))

        return {
            'survivability': survivability,
            'damage_efficiency': damage_efficiency
        }

    def _calculate_session_duration(self) -> float:
        """Calculate total session duration in seconds."""
        events = self.data.get('events', [])
        if not events:
            return 0

        start_time = self.data['start_time']
        end_time = events[-1]['timestamp']
        duration = end_time - start_time

        if duration < 0:
            raise ValueError(f"Invalid session: end_time ({end_time}) < start_time ({start_time})")

        # Return actual duration, even if very short
        # Callers must handle division by zero explicitly
        return duration

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
        """Calculate how aggressive the player is.

        Aggressive = pursues enemies, close-range combat, high mobility, rushes in.
        """
        score = 0.0

        # Pursuit movement - PRIMARY indicator of aggressive play
        if self.features.get('pursuit_pct', 0) > self.THRESHOLDS['pursuit_pct']['high']:
            score += 0.35  # Main indicator
        elif self.features.get('pursuit_pct', 0) > self.THRESHOLDS['pursuit_pct']['medium']:
            score += 0.2

        # Close combat preference
        if self.features['avg_enemy_distance'] < self.THRESHOLDS['avg_enemy_distance']['close']:
            score += 0.25

        # High aggression rate (kills per second)
        if self.features['aggression_score'] > self.THRESHOLDS['aggression']['high']:
            score += 0.2

        # High mobility (rushing around)
        if self.features['mobility_index'] > self.THRESHOLDS['mobility_index']['medium']:
            score += 0.1

        # Low cover usage (optional - rushes in the open)
        if self.features['cover_usage_pct'] < self.THRESHOLDS['cover_usage']['low']:
            score += 0.1

        return min(score, 1.0)

    def _calculate_defensive_score(self) -> float:
        """Calculate how defensive/cautious the player is.

        Defensive = tactical retreat, maintains distance, uses cover, prioritizes survival.
        Movement is AWAY from enemies to reposition, not toward them.
        """
        score = 0.0

        # Retreat movement - PRIMARY indicator of defensive play
        if self.features.get('retreat_pct', 0) > self.THRESHOLDS['retreat_pct']['high']:
            score += 0.35  # Main indicator: retreating to reposition
        elif self.features.get('retreat_pct', 0) > self.THRESHOLDS['retreat_pct']['medium']:
            score += 0.2

        # Maintains distance from enemies
        if self.features['avg_enemy_distance'] > self.THRESHOLDS['avg_enemy_distance']['far']:
            score += 0.25
        elif self.features['avg_enemy_distance'] > self.THRESHOLDS['avg_enemy_distance']['medium']:
            score += 0.15

        # Low damage taken (good survivability)
        if self.features['survivability'] < self.THRESHOLDS['survivability_rate']['excellent']:
            score += 0.2

        # Cover usage when available
        if self.features['cover_usage_pct'] > self.THRESHOLDS['cover_usage']['medium']:
            score += 0.15

        # Good accuracy (patient, deliberate shots from safe positions)
        if self.features['shot_accuracy'] > self.THRESHOLDS['shot_accuracy']['good']:
            score += 0.05

        return min(score, 1.0)


    def _calculate_chaotic_score(self) -> float:
        """Calculate chaotic/panicked playstyle.

        Chaotic = no clear strategy, inconsistent movement, poor accuracy, medium range,
        neither retreating strategically nor pursuing aggressively.
        """
        score = 0.0

        # Poor accuracy - key indicator of panic/chaos
        if self.features['shot_accuracy'] < self.THRESHOLDS['shot_accuracy']['poor']:
            score += 0.3

        # High damage taken (poor survivability)
        if self.features['survivability'] > self.THRESHOLDS['survivability_rate']['poor']:
            score += 0.25

        # Poor damage efficiency
        if self.features['damage_efficiency'] < self.THRESHOLDS['damage_efficiency']['poor']:
            score += 0.2

        # No clear movement pattern - neither retreating nor pursuing consistently
        retreat = self.features.get('retreat_pct', 0)
        pursuit = self.features.get('pursuit_pct', 0)
        if retreat < self.THRESHOLDS['retreat_pct']['medium'] and pursuit < self.THRESHOLDS['pursuit_pct']['medium']:
            score += 0.15  # Erratic/unfocused movement

        # Medium distance combat (not committing to either close or far)
        if (self.features['avg_enemy_distance'] >= self.THRESHOLDS['avg_enemy_distance']['close'] and
            self.features['avg_enemy_distance'] <= self.THRESHOLDS['avg_enemy_distance']['far']):
            score += 0.1

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

Spatial Behavior:
  - Avg Enemy Distance:   {self.features['avg_enemy_distance']:.1f} pixels
  - Cover Usage:          {self.features['cover_usage_pct']*100:.1f}%
  - Distance Traveled:    {self.features['distance_traveled']:.1f} pixels
  - Mobility Index:       {self.features['mobility_index']:.1f} px/sec

Movement Patterns:
  - Retreat Movement:     {self.features.get('retreat_pct', 0)*100:.1f}% (moving away from enemies)
  - Pursuit Movement:     {self.features.get('pursuit_pct', 0)*100:.1f}% (moving toward enemies)
  - Neutral Movement:     {(1 - self.features.get('retreat_pct', 0) - self.features.get('pursuit_pct', 0))*100:.1f}% (sideways/stationary)

Aggression Metrics:
  - Kills per Second:     {self.features['aggression_score']:.3f}
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

    def save_classification(self, output_filepath: str):
        """Save classification results to JSON file."""
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

        with open(output_filepath, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"Classification saved to {output_filepath}")


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

    # Create output directory
    output_dir = os.path.join("analysis_results", expected_playstyle)
    os.makedirs(output_dir, exist_ok=True)

    for filepath in json_files:
        try:
            print(f"\nAnalyzing: {os.path.basename(filepath)}")

            # Analyze file
            analyzer = GameplayAnalyzer(filepath)
            analyzer.extract_features()
            analyzer.classify_behavior()

            # Save individual analysis
            output_file = os.path.join(output_dir, f"analysis_{analyzer.data['session_id']}.json")
            analyzer.save_classification(output_file)

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

    # Save aggregate report
    aggregate_file = os.path.join(output_dir, "aggregate_report.txt")
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


def main():
    """Main entry point for standalone usage."""
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file: python analyze_player_behavior.py <gameplay_data.json>")
        print("  Directory:   python analyze_player_behavior.py --dir <directory_path>")
        print("\nExamples:")
        print("  python analyze_player_behavior.py gameplay_data_20250922_154913.json")
        print("  python analyze_player_behavior.py --dir gameplay_data/defensive")
        sys.exit(1)

    # Check for directory mode
    if sys.argv[1] == "--dir":
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

            # Save classification to file
            label = analyzer.data.get('playstyle_label')
            if label:
                output_dir = os.path.join("analysis_results", label)
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, f"analysis_{analyzer.data['session_id']}.json")
            else:
                output_file = f"analysis_{analyzer.data['session_id']}.json"

            analyzer.save_classification(output_file)

        except Exception as e:
            print(f"Error analyzing gameplay data: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()