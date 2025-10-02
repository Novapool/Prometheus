import pygame
import math
import random
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
LIME = (50, 255, 50)

def check_circle_rect_collision(circle_x, circle_y, circle_radius, rect):
    """Check if a circle collides with a rectangle."""
    # Find closest point on rectangle to circle center
    closest_x = max(rect.left, min(circle_x, rect.right))
    closest_y = max(rect.top, min(circle_y, rect.bottom))

    # Calculate distance from circle center to closest point
    distance = math.sqrt((circle_x - closest_x)**2 + (circle_y - closest_y)**2)
    return distance < circle_radius

class DataLogger:
    def __init__(self, playstyle_label=None):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.playstyle_label = playstyle_label
        self.game_data = {
            'session_id': self.session_id,
            'playstyle_label': playstyle_label,
            'start_time': time.time(),
            'events': [],
            'player_stats': {
                'total_damage_dealt': 0,
                'total_damage_taken': 0,
                'shots_fired': 0,
                'shots_hit': 0,
                'enemies_killed': 0,
                'time_in_cover': 0,
                'distance_traveled': 0,
                'reloads': 0,
                'retreat_frames': 0,
                'pursuit_frames': 0,
                'neutral_frames': 0
            },
            'behavioral_metrics': [],
            'combat_decisions': [],
            'threat_responses': [],
            'movement_patterns': []
        }
        self.last_cover_check_time = time.time()
        self.was_in_cover = False
        self.frame_count = 0
        self.movement_sample_counter = 0
        
    def log_event(self, event_type: str, data: Dict):
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'data': data
        }
        self.game_data['events'].append(event)
        
    def log_frame_data(self, player, enemies, cover_objects):
        # Calculate behavioral metrics every frame
        current_time = time.time()
        using_cover = self._check_using_cover((player.x, player.y), enemies, cover_objects)

        # Track time in cover - only count if ALREADY in cover
        time_delta = current_time - self.last_cover_check_time
        if using_cover and self.was_in_cover:
            self.game_data['player_stats']['time_in_cover'] += time_delta

        self.was_in_cover = using_cover
        self.last_cover_check_time = current_time

        # Track movement direction relative to enemies
        movement_direction = self._calculate_movement_direction(player, enemies)
        if movement_direction == 'retreat':
            self.game_data['player_stats']['retreat_frames'] += 1
        elif movement_direction == 'pursuit':
            self.game_data['player_stats']['pursuit_frames'] += 1
        else:
            self.game_data['player_stats']['neutral_frames'] += 1

        frame_data = {
            'timestamp': current_time,
            'player_position': (player.x, player.y),
            'player_health': player.health,
            'player_ammo': player.ammo,
            'enemies_count': len(enemies),
            'avg_enemy_distance': self._calculate_avg_enemy_distance((player.x, player.y), enemies),
            'nearest_enemy_distance': self._calculate_nearest_enemy_distance((player.x, player.y), enemies),
            'near_cover': self._check_near_cover((player.x, player.y), cover_objects),
            'using_cover': using_cover,
            'is_reloading': player.is_reloading,
            'movement_direction': movement_direction
        }

        # Only log every 10 frames to avoid excessive data
        self.frame_count += 1
        if self.frame_count % 10 == 0:
            self.game_data['behavioral_metrics'].append(frame_data)
    
    def _calculate_avg_enemy_distance(self, player_pos, enemies):
        if not enemies:
            return 0
        total_distance = sum(math.sqrt((enemy.x - player_pos[0])**2 + (enemy.y - player_pos[1])**2) for enemy in enemies)
        return total_distance / len(enemies)
    
    def _calculate_nearest_enemy_distance(self, player_pos, enemies):
        if not enemies:
            return float('inf')
        distances = [math.sqrt((enemy.x - player_pos[0])**2 + (enemy.y - player_pos[1])**2) for enemy in enemies]
        return min(distances)
    
    def _check_near_cover(self, player_pos, cover_objects, threshold=50):
        """Simple proximity check - kept for backwards compatibility."""
        for cover in cover_objects:
            distance = math.sqrt((cover.x - player_pos[0])**2 + (cover.y - player_pos[1])**2)
            if distance < threshold:
                return True
        return False

    def _check_using_cover(self, player_pos, enemies, cover_objects):
        """More forgiving cover detection."""
        if not enemies:
            return False
        
        for cover in cover_objects:
            # More generous distance threshold
            player_to_cover_dist = math.sqrt(
                (cover.x - player_pos[0])**2 + (cover.y - player_pos[1])**2
            )
            
            # If player is reasonably close to cover (within 100 pixels)
            if player_to_cover_dist <= 100:
                # Check if cover is between player and ANY enemy
                for enemy in enemies:
                    enemy_to_player_angle = math.atan2(
                        player_pos[1] - enemy.y,
                        player_pos[0] - enemy.x
                    )
                    enemy_to_cover_angle = math.atan2(
                        cover.y - enemy.y,
                        cover.x - enemy.x
                    )
                    
                    # If angles are similar (within 45 degrees), player is using cover
                    angle_diff = abs(enemy_to_player_angle - enemy_to_cover_angle)
                    if angle_diff < 0.785:  # ~45 degrees
                        return True
        
        return False

    def _is_cover_between(self, point_a, point_b, cover):
        """Check if cover blocks line between two points using line-rectangle intersection."""
        # Pygame's clipline returns empty list if no intersection
        result = cover.rect.clipline(point_a, point_b)
        return len(result) > 0

    def _calculate_movement_direction(self, player, enemies):
        """Determine if player is moving toward, away, or neutral relative to nearest enemy.

        Returns:
            'pursuit': Moving toward enemies (aggressive)
            'retreat': Moving away from enemies (defensive)
            'neutral': Stationary or no clear direction
        """
        if not enemies:
            return 'neutral'

        # Get player velocity magnitude
        velocity_mag = math.sqrt(player.velocity[0]**2 + player.velocity[1]**2)

        # If barely moving, it's neutral
        if velocity_mag < 1.0:  # Less than 1 pixel per frame
            return 'neutral'

        # Find nearest enemy
        nearest_enemy = min(enemies, key=lambda e: math.sqrt((e.x - player.x)**2 + (e.y - player.y)**2))

        # Vector from player to nearest enemy
        to_enemy_x = nearest_enemy.x - player.x
        to_enemy_y = nearest_enemy.y - player.y
        to_enemy_mag = math.sqrt(to_enemy_x**2 + to_enemy_y**2)

        if to_enemy_mag < 0.1:
            return 'neutral'

        # Normalize vectors
        to_enemy_x /= to_enemy_mag
        to_enemy_y /= to_enemy_mag
        vel_x = player.velocity[0] / velocity_mag
        vel_y = player.velocity[1] / velocity_mag

        # Dot product: positive = moving toward, negative = moving away
        dot_product = vel_x * to_enemy_x + vel_y * to_enemy_y

        # Threshold for determining direction (0.3 = ~72 degree cone)
        if dot_product > 0.3:
            return 'pursuit'
        elif dot_product < -0.3:
            return 'retreat'
        else:
            return 'neutral'  # Moving perpendicular/sideways
    
    def log_combat_decision(self, decision_type: str, context: Dict):
        """Track key combat decisions and their context."""
        self.game_data['combat_decisions'].append({
            'timestamp': time.time(),
            'decision': decision_type,
            'context': context
        })

    def log_threat_response(self, player, enemies):
        """Track how player responds to different threat levels."""
        if not enemies:
            return

        player_pos = (player.x, player.y)

        # Calculate threat level
        nearby_enemies = [e for e in enemies
                         if math.sqrt((e.x - player.x)**2 + (e.y - player.y)**2) < 250]
        threat_level = len(nearby_enemies)

        # Calculate nearest enemy
        nearest_dist = min([math.sqrt((e.x - player.x)**2 + (e.y - player.y)**2)
                           for e in enemies])

        # Determine player's response based on velocity
        velocity_mag = math.sqrt(player.velocity[0]**2 + player.velocity[1]**2)

        if velocity_mag < 0.5:
            response = "defensive"
        else:
            # Check if moving toward or away from nearest enemy
            nearest_enemy = min(enemies, key=lambda e: math.sqrt((e.x - player.x)**2 + (e.y - player.y)**2))
            direction_to_enemy = (nearest_enemy.x - player.x, nearest_enemy.y - player.y)

            # Dot product to determine if moving toward enemy
            dot = player.velocity[0] * direction_to_enemy[0] + player.velocity[1] * direction_to_enemy[1]

            if dot > 0:
                response = "aggressive"
            else:
                response = "retreating"

        # Only log every 2 seconds to avoid spam
        if len(self.game_data['threat_responses']) == 0 or \
           time.time() - self.game_data['threat_responses'][-1]['timestamp'] > 2.0:
            self.game_data['threat_responses'].append({
                'timestamp': time.time(),
                'threat_level': threat_level,
                'nearest_enemy_distance': nearest_dist,
                'player_health_pct': player.health / player.max_health,
                'response': response,
                'velocity_magnitude': velocity_mag
            })

    def log_movement_pattern(self, player):
        """Track movement patterns over time."""
        velocity_mag = math.sqrt(player.velocity[0]**2 + player.velocity[1]**2)

        # Only log if there's actual movement
        if velocity_mag > 0.1:
            self.game_data['movement_patterns'].append({
                'timestamp': time.time(),
                'position': (player.x, player.y),
                'velocity': player.velocity,
                'velocity_magnitude': velocity_mag,
                'health': player.health
            })

    def save_data(self):
        import os

        # Create directory structure if it doesn't exist
        if self.playstyle_label:
            directory = os.path.join("gameplay_data", self.playstyle_label)
            os.makedirs(directory, exist_ok=True)
            filename = os.path.join(directory, f"gameplay_data_{self.session_id}.json")
        else:
            # Fallback if no label provided
            filename = f"gameplay_data_{self.session_id}.json"

        with open(filename, 'w') as f:
            json.dump(self.game_data, f, indent=2)
        print(f"Data saved to {filename}")

class Bullet:
    def __init__(self, x, y, angle, speed=500, owner="player"):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.owner = owner
        self.radius = 3
        
    def update(self, dt):
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt
        
    def draw(self, screen):
        color = LIME if self.owner == "player" else RED
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        
    def is_off_screen(self):
        return (self.x < 0 or self.x > SCREEN_WIDTH or 
                self.y < 0 or self.y > SCREEN_HEIGHT)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15
        self.speed = 200
        self.health = 100
        self.max_health = 100
        self.ammo = 30
        self.max_ammo = 30
        self.last_shot_time = 0
        self.shot_cooldown = 0.2
        self.last_position = (x, y)
        self.is_reloading = False
        self.reload_time = 1.5  # seconds
        self.reload_start_time = 0
        self.last_health = 100
        self.velocity = (0, 0)

    @property
    def velocity_magnitude(self):
        """Calculate velocity magnitude."""
        return math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)

    @property
    def health_percent(self):
        """Calculate health as percentage."""
        return self.health / self.max_health

    def update(self, dt, keys, mouse_pos, cover_objects, current_time, data_logger):
        # Store last position for distance calculation
        self.last_position = (self.x, self.y)

        # Handle reload
        if self.is_reloading:
            if current_time - self.reload_start_time >= self.reload_time:
                self.ammo = self.max_ammo
                self.is_reloading = False
                # Log reload completion
                data_logger.log_event("reload_complete", {
                    'duration': current_time - self.reload_start_time,
                    'health': self.health,
                    'position': (self.x, self.y)
                })

        # Movement
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        # Calculate new position
        new_x = self.x + dx * self.speed * dt
        new_y = self.y + dy * self.speed * dt

        # Check collision with cover objects using circle-rectangle collision
        collision = False
        for cover in cover_objects:
            if check_circle_rect_collision(new_x, new_y, self.radius, cover.rect):
                collision = True
                break

        # Only move if no collision
        if not collision:
            self.x = new_x
            self.y = new_y

        # Keep player on screen
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

        # Track velocity for behavioral analysis
        self.velocity = (self.x - self.last_position[0], self.y - self.last_position[1])
        
    def shoot(self, mouse_pos, current_time, data_logger):
        if self.is_reloading:
            return None

        if (current_time - self.last_shot_time > self.shot_cooldown and
            self.ammo > 0):

            angle = math.atan2(mouse_pos[1] - self.y, mouse_pos[0] - self.x)
            bullet = Bullet(self.x, self.y, angle, owner="player")

            self.ammo -= 1
            self.last_shot_time = current_time

            # Log shot event
            data_logger.log_event("shot_fired", {
                'position': (self.x, self.y),
                'target_position': mouse_pos,
                'ammo_remaining': self.ammo,
                'angle': angle,
                'health': self.health
            })
            data_logger.game_data['player_stats']['shots_fired'] += 1

            return bullet
        return None

    def start_reload(self, current_time, data_logger, enemies):
        if not self.is_reloading and self.ammo < self.max_ammo:
            self.is_reloading = True
            self.reload_start_time = current_time

            # Calculate nearby enemies for context
            nearby_enemies = len([e for e in enemies
                                if math.sqrt((e.x - self.x)**2 + (e.y - self.y)**2) < 200])

            data_logger.log_event("reload_start", {
                'ammo_remaining': self.ammo,
                'health': self.health,
                'enemies_nearby': nearby_enemies,
                'position': (self.x, self.y)
            })
            data_logger.game_data['player_stats']['reloads'] += 1
        
    def take_damage(self, damage, data_logger):
        old_health = self.health
        self.health -= damage
        data_logger.game_data['player_stats']['total_damage_taken'] += damage

        # Check if crossed health threshold
        health_pct_before = old_health / self.max_health
        health_pct_after = self.health / self.max_health

        threshold_crossed = None
        if health_pct_before > 0.75 and health_pct_after <= 0.75:
            threshold_crossed = "75%"
        elif health_pct_before > 0.5 and health_pct_after <= 0.5:
            threshold_crossed = "50%"
        elif health_pct_before > 0.25 and health_pct_after <= 0.25:
            threshold_crossed = "25%"

        data_logger.log_event("player_damaged", {
            'damage': damage,
            'health_remaining': self.health,
            'health_pct': health_pct_after,
            'position': (self.x, self.y),
            'velocity_magnitude': math.sqrt(self.velocity[0]**2 + self.velocity[1]**2),
            'threshold_crossed': threshold_crossed,
            'is_reloading': self.is_reloading
        })

        # Log combat decision if health is critical
        if health_pct_after < 0.3 and health_pct_before >= 0.3:
            data_logger.log_combat_decision("critical_health", {
                'health': self.health,
                'ammo': self.ammo,
                'position': (self.x, self.y)
            })
        
    def get_distance_traveled(self):
        return math.sqrt((self.x - self.last_position[0])**2 + (self.y - self.last_position[1])**2)
        
    def draw(self, screen):
        # Player circle
        pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), self.radius)
        
        # Health bar
        bar_width = 40
        bar_height = 6
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.radius - 15
        
        # Background
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        # Health
        health_width = (self.health / self.max_health) * bar_width
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))

class Enemy:
    def __init__(self, x, y, enemy_type="basic"):
        self.x = x
        self.y = y
        self.radius = 12
        self.speed = 80
        self.health = 30
        self.max_health = 30
        self.last_shot_time = 0
        self.shot_cooldown = 1.5
        self.enemy_type = enemy_type
        self.target_distance = 150 if enemy_type == "sniper" else 80
        
    def update(self, dt, player, data_logger, cover_objects):
        # Calculate distance to player
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)

        # Prevent division by zero if enemy spawns on player
        if distance < 0.1:
            return

        # Calculate desired movement based on AI type
        move_x = 0
        move_y = 0

        if self.enemy_type == "basic":
            # Move towards player
            if distance > self.target_distance:
                move_x = (dx/distance) * self.speed * dt
                move_y = (dy/distance) * self.speed * dt
        elif self.enemy_type == "sniper":
            # Maintain distance, strafe occasionally
            if distance < self.target_distance:
                move_x = -(dx/distance) * self.speed * dt * 0.5
                move_y = -(dy/distance) * self.speed * dt * 0.5

        # Calculate new position
        new_x = self.x + move_x
        new_y = self.y + move_y

        # Check collision with cover objects using circle-rectangle collision
        collision = False
        blocking_cover = None
        for cover in cover_objects:
            if check_circle_rect_collision(new_x, new_y, self.radius, cover.rect):
                collision = True
                blocking_cover = cover
                break

        # If collision detected, try to slide around the obstacle
        if collision:
            # Try moving only horizontally
            test_x = self.x + move_x
            test_y = self.y
            can_move_x = not check_circle_rect_collision(test_x, test_y, self.radius, blocking_cover.rect)

            # Try moving only vertically
            test_x = self.x
            test_y = self.y + move_y
            can_move_y = not check_circle_rect_collision(test_x, test_y, self.radius, blocking_cover.rect)

            # Apply sliding movement
            if can_move_x:
                new_x = self.x + move_x
                new_y = self.y
            elif can_move_y:
                new_x = self.x
                new_y = self.y + move_y
            else:
                # Can't move at all, try perpendicular movement to unstick
                perpendicular_x = -move_y  # Rotate 90 degrees
                perpendicular_y = move_x

                test_x = self.x + perpendicular_x
                test_y = self.y + perpendicular_y

                # Check if perpendicular movement is safe
                perpendicular_safe = True
                for cover in cover_objects:
                    if check_circle_rect_collision(test_x, test_y, self.radius, cover.rect):
                        perpendicular_safe = False
                        break

                if perpendicular_safe:
                    new_x = test_x
                    new_y = test_y
                else:
                    # Completely stuck, don't move
                    new_x = self.x
                    new_y = self.y

        # Final collision check with all cover objects
        final_collision = False
        for cover in cover_objects:
            if check_circle_rect_collision(new_x, new_y, self.radius, cover.rect):
                final_collision = True
                break

        # Only update position if no collision
        if not final_collision:
            self.x = new_x
            self.y = new_y

        # Keep enemy on screen
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))
        
    def shoot(self, player, current_time):
        if current_time - self.last_shot_time > self.shot_cooldown:
            angle = math.atan2(player.y - self.y, player.x - self.x)
            bullet = Bullet(self.x, self.y, angle, speed=300, owner="enemy")
            self.last_shot_time = current_time
            return bullet
        return None
        
    def take_damage(self, damage, data_logger):
        # Cap damage at remaining health to prevent negative health
        actual_damage = min(damage, self.health)
        self.health -= actual_damage
        data_logger.game_data['player_stats']['total_damage_dealt'] += actual_damage

        if self.health <= 0:
            data_logger.game_data['player_stats']['enemies_killed'] += 1
            data_logger.log_event("enemy_killed", {
                'enemy_type': self.enemy_type,
                'position': (self.x, self.y)
            })
        
    def draw(self, screen):
        # Enemy circle
        color = DARK_GRAY if self.enemy_type == "sniper" else RED
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        
        # Health bar
        bar_width = 30
        bar_height = 4
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.radius - 10
        
        # Background
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        # Health
        health_width = (self.health / self.max_health) * bar_width
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))

class CoverObject:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x - width//2, y - height//2, width, height)

    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.rect)

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font_title = pygame.font.Font(None, 64)
        self.font_button = pygame.font.Font(None, 42)
        self.font_desc = pygame.font.Font(None, 28)

        # Button definitions: (text, playstyle_label, description)
        self.buttons = [
            ("Play as DEFENSIVE", "defensive", "Use cover, maintain distance, prioritize survival"),
            ("Play as AGGRESSIVE", "aggressive", "Rush enemies, close combat, high damage output"),
            ("Play as CHAOTIC", "chaotic", "Unpredictable movement, reactive, experimental tactics"),
            ("Exit", None, "Quit the program")
        ]

        self.button_rects = []
        self.hovered_button = None

    def run(self):
        """Run the menu loop and return selected playstyle or None to exit."""
        # Calculate button positions
        button_width = 600
        button_height = 70
        button_spacing = 30
        start_y = 250

        self.button_rects = []
        for i in range(len(self.buttons)):
            x = SCREEN_WIDTH // 2 - button_width // 2
            y = start_y + i * (button_height + button_spacing)
            self.button_rects.append(pygame.Rect(x, y, button_width, button_height))

        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()

            # Update hovered button
            self.hovered_button = None
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(mouse_pos):
                    self.hovered_button = i
                    break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        for i, rect in enumerate(self.button_rects):
                            if rect.collidepoint(mouse_pos):
                                _, playstyle, _ = self.buttons[i]
                                return playstyle  # Returns None for Exit button

            self.draw()
            pygame.display.flip()
            pygame.time.Clock().tick(60)

        return None

    def draw(self):
        self.screen.fill(WHITE)

        # Title
        title = self.font_title.render("Adaptive Combat AI", True, BLACK)
        subtitle = self.font_button.render("Data Collection Mode", True, DARK_GRAY)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 150))

        # Instructions
        instruction = self.font_desc.render("Select your intended playstyle to begin:", True, BLACK)
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 200))

        # Draw buttons
        for i, (button_text, playstyle, description) in enumerate(self.buttons):
            rect = self.button_rects[i]

            # Button background
            if self.hovered_button == i:
                color = CYAN if playstyle else RED
                border_width = 4
            else:
                color = BLUE if playstyle else DARK_GRAY
                border_width = 2

            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, BLACK, rect, border_width, border_radius=10)

            # Button text
            text = self.font_button.render(button_text, True, WHITE)
            text_x = rect.centerx - text.get_width() // 2
            text_y = rect.centery - text.get_height() // 2
            self.screen.blit(text, (text_x, text_y))

            # Description below button
            if playstyle:  # Don't show description for Exit button
                desc = self.font_desc.render(description, True, DARK_GRAY)
                desc_x = rect.centerx - desc.get_width() // 2
                desc_y = rect.bottom + 8
                self.screen.blit(desc, (desc_x, desc_y))

class Game:
    def __init__(self, screen, playstyle_label):
        self.screen = screen
        pygame.display.set_caption("Adaptive Combat AI - Data Collection")
        self.clock = pygame.time.Clock()

        # Game objects
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.enemies = []
        self.bullets = []
        self.cover_objects = []

        # Data logging
        self.data_logger = DataLogger(playstyle_label)

        # Game state
        self.wave = 1
        self.enemies_spawned = 0
        self.max_enemies_per_wave = 3

        # Create cover objects
        self.create_cover()

        # Spawn initial enemies
        self.spawn_enemies()
        
    def create_cover(self):
        # Create some scattered cover objects
        cover_positions = [
            (200, 200, 60, 20),
            (800, 150, 20, 80),
            (150, 600, 80, 30),
            (700, 550, 40, 40),
            (500, 300, 30, 60),
            (300, 450, 70, 25)
        ]
        
        for x, y, w, h in cover_positions:
            self.cover_objects.append(CoverObject(x, y, w, h))
            
    def spawn_enemies(self):
        for _ in range(self.max_enemies_per_wave):
            # Spawn enemies at random positions away from player
            while True:
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = random.randint(50, SCREEN_HEIGHT - 50)
                distance = math.sqrt((x - self.player.x)**2 + (y - self.player.y)**2)
                if distance > 200:  # Ensure enemies spawn away from player
                    enemy_type = random.choice(["basic", "basic", "sniper"])  # 2/3 basic, 1/3 sniper
                    self.enemies.append(Enemy(x, y, enemy_type))
                    break
                    
    def handle_collisions(self):
        # Bullet vs enemy collisions
        for bullet in self.bullets[:]:
            if bullet.owner == "player":
                for enemy in self.enemies[:]:
                    distance = math.sqrt((bullet.x - enemy.x)**2 + (bullet.y - enemy.y)**2)
                    if distance < bullet.radius + enemy.radius:
                        enemy.take_damage(10, self.data_logger)
                        self.bullets.remove(bullet)
                        self.data_logger.game_data['player_stats']['shots_hit'] += 1
                        
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                        break
                        
        # Bullet vs player collisions
        for bullet in self.bullets[:]:
            if bullet.owner == "enemy":
                distance = math.sqrt((bullet.x - self.player.x)**2 + (bullet.y - self.player.y)**2)
                if distance < bullet.radius + self.player.radius:
                    self.player.take_damage(15, self.data_logger)
                    self.bullets.remove(bullet)
                    
        # Bullet vs cover collisions (asymmetric: only enemy bullets blocked)
        for bullet in self.bullets[:]:
            if bullet.owner == "enemy":  # Only enemy bullets are blocked by cover
                for cover in self.cover_objects:
                    if cover.rect.collidepoint(bullet.x, bullet.y):
                        self.bullets.remove(bullet)
                        break
            # Player bullets pierce through cover (no collision check)
                    
    def update(self, dt):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        current_time = time.time()

        # Update player
        self.player.update(dt, keys, mouse_pos, self.cover_objects, current_time, self.data_logger)

        # Update enemies
        for enemy in self.enemies:
            enemy.update(dt, self.player, self.data_logger, self.cover_objects)

            # Enemy shooting
            bullet = enemy.shoot(self.player, current_time)
            if bullet:
                self.bullets.append(bullet)

        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if bullet.is_off_screen():
                self.bullets.remove(bullet)

        # Handle collisions
        self.handle_collisions()

        # Log frame data (now passes player object)
        self.data_logger.log_frame_data(self.player, self.enemies, self.cover_objects)

        # Track distance traveled
        self.data_logger.game_data['player_stats']['distance_traveled'] += self.player.get_distance_traveled()

        # Log threat response (every ~2 seconds via internal throttling)
        self.data_logger.log_threat_response(self.player, self.enemies)

        # Log movement patterns (fixed sampling - every 30 frames)
        self.data_logger.movement_sample_counter += 1
        if self.data_logger.movement_sample_counter >= 30:
            self.data_logger.log_movement_pattern(self.player)
            self.data_logger.movement_sample_counter = 0

        # Check if wave is complete
        if not self.enemies and self.wave < 10:  # Limit to 10 waves for testing
            self.wave += 1
            self.max_enemies_per_wave = min(6, 2 + self.wave)  # Gradually increase difficulty
            self.spawn_enemies()
            self.data_logger.log_event("wave_complete", {'wave': self.wave - 1})
            
    def draw(self):
        self.screen.fill(WHITE)
        
        # Draw cover objects
        for cover in self.cover_objects:
            cover.draw(self.screen)
            
        # Draw game objects
        self.player.draw(self.screen)
        
        for enemy in self.enemies:
            enemy.draw(self.screen)
            
        for bullet in self.bullets:
            bullet.draw(self.screen)
            
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
        
    def draw_ui(self):
        font = pygame.font.Font(None, 36)
        
        # Health
        health_text = font.render(f"Health: {self.player.health}", True, BLACK)
        self.screen.blit(health_text, (10, 10))
        
        # Ammo
        ammo_text = font.render(f"Ammo: {self.player.ammo}", True, BLACK)
        self.screen.blit(ammo_text, (10, 50))
        
        # Wave
        wave_text = font.render(f"Wave: {self.wave}", True, BLACK)
        self.screen.blit(wave_text, (10, 90))
        
        # Enemies remaining
        enemies_text = font.render(f"Enemies: {len(self.enemies)}", True, BLACK)
        self.screen.blit(enemies_text, (10, 130))
        
        # Instructions
        font_small = pygame.font.Font(None, 24)
        instructions = [
            "WASD: Move",
            "Mouse: Aim",
            "Left Click: Shoot",
            "R: Reload",
            "ESC: Quit & Save Data"
        ]

        for i, instruction in enumerate(instructions):
            text = font_small.render(instruction, True, BLACK)
            self.screen.blit(text, (SCREEN_WIDTH - 200, 10 + i * 25))

        # Show reload status if reloading
        if self.player.is_reloading:
            reload_text = font.render("RELOADING...", True, RED)
            self.screen.blit(reload_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2))
            
    def run(self):
        """Run the game loop. Returns True to return to menu, False to exit program."""
        running = True
        return_to_menu = True

        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return_to_menu = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        return_to_menu = True
                    elif event.key == pygame.K_r:  # R key to reload
                        self.player.start_reload(time.time(), self.data_logger, self.enemies)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        bullet = self.player.shoot(pygame.mouse.get_pos(), time.time(), self.data_logger)
                        if bullet:
                            self.bullets.append(bullet)

            # Check game over conditions
            if self.player.health <= 0:
                self.data_logger.log_event("game_over", {"reason": "player_died", "wave": self.wave})
                self.show_game_over_screen("Game Over - You Died!")
                running = False
            elif self.wave > 10:
                self.data_logger.log_event("game_complete", {"waves_completed": self.wave})
                self.show_game_over_screen("Victory - All Waves Complete!")
                running = False

            if running:
                self.update(dt)
                self.draw()

        # Save data before returning
        self.data_logger.save_data()
        return return_to_menu

    def show_game_over_screen(self, message):
        """Display game over message briefly."""
        font_large = pygame.font.Font(None, 72)
        font_small = pygame.font.Font(None, 36)

        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Main message
        text = font_large.render(message, True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

        # Return message
        return_text = font_small.render("Returning to menu...", True, WHITE)
        self.screen.blit(return_text, (SCREEN_WIDTH // 2 - return_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

        pygame.display.flip()
        pygame.time.wait(2500)  # Wait 2.5 seconds

def main():
    """Main entry point with menu loop."""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    menu = Menu(screen)

    while True:
        # Show menu and get playstyle selection
        playstyle = menu.run()

        # Exit if user chose to quit
        if playstyle is None:
            break

        # Run game with selected playstyle
        game = Game(screen, playstyle)
        return_to_menu = game.run()

        # Exit if user closed window during game
        if not return_to_menu:
            break

    pygame.quit()

if __name__ == "__main__":
    main()