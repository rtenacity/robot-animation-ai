from manim import Scene, Square, Circle, BLUE, RED, GREEN, MoveAlongPath, Line, NumberPlane, BLACK, config, WHITE, AnimationGroup, ApplyMethod, UP, DOWN, LEFT, Rectangle, Text

config.pixel_height = 1920
config.pixel_width = 1920
config.frame_height = 16.0
config.frame_width = 16.0
config.background_color = WHITE

class Bot:
    def __init__(self, scene, color, initial_position):
        self.scene = scene
        grid_space_scale = 0.2
        self.box = Square(color=color).scale(3*grid_space_scale)
        self.box.move_to(self._grid_to_scene_coords(initial_position))
        self.held_item = None  
        self.position = (50, 50)
        
    def move(self, speed, direction, time):
        dx, dy = direction
        if dx != 0:  # Moving horizontally
            if dx > 0:
                max_distance_x = 100 - self.position[0]  # Right
            else:
                max_distance_x = self.position[0]  # Left
            time_x = abs(max_distance_x / (speed * dx))  # Use abs to ensure positive time
        else:
            time_x = float('inf')  # Not moving horizontally
        
        if dy != 0:  # Moving vertically
            if dy > 0:
                max_distance_y = 100 - self.position[1]  # Up
            else:
                max_distance_y = self.position[1]  # Down
            time_y = abs(max_distance_y / (speed * dy))  # Use abs to ensure positive time
        else:
            time_y = float('inf')  # Not moving vertically

        actual_time = min(time, time_x, time_y)

        # Calculate new position based on the actual time
        new_x = self.position[0] + dx * speed * actual_time
        new_y = self.position[1] + dy * speed * actual_time

        # Ensure the new position is within bounds
        new_x = max(0, min(new_x, 100))
        new_y = max(0, min(new_y, 100))

        # Update the robot's position
        self.position = (new_x, new_y)
        return self.move_to_point(self.position, run_time=actual_time)  



    def move_to_point(self, point, run_time=2):
        target_position = self._grid_to_scene_coords(point)
        bot_move_animation = ApplyMethod(self.box.move_to, target_position)
        
        self.position = point

        if self.held_item is not None:
            item_move_animation = ApplyMethod(self.held_item.item.move_to, target_position)
            self.scene.play(AnimationGroup(bot_move_animation, item_move_animation, lag_ratio=0))
        else:
            self.scene.play(bot_move_animation)
    
    def pick_up_item(self, item):
        item_position = item.position  # Get the item's position
        if not self._is_close_to(item):
            # If not close, move the robot to the item's position
            self.move_to_point(item_position, run_time=2)

        if self._is_close_to(item):
            self.held_item = item
            item.being_held = True
            bot_center = self.box.get_center()
            pick_up_animation = ApplyMethod(item.item.move_to, bot_center)
            self.scene.play(pick_up_animation)
            self.scene.wait(1)
        else:
            print("Error: Could not move close enough to pick up the item.")

    def place_item(self, new_position):
        if self.held_item is not None:
            animation = ApplyMethod(self.held_item.item.move_to, self._grid_to_scene_coords(new_position))
            self.held_item.being_held = False
            self.held_item = None
            self.scene.play(animation)
            self.scene.wait(1)

    def _is_close_to(self, item):
        bot_pos = self.box.get_center()
        item_pos = item.item.get_center()
        return abs(bot_pos[0] - item_pos[0]) <= 1 and abs(bot_pos[1] - item_pos[1]) <= 1

    def _grid_to_scene_coords(self, point):
        x, y = point
        scene_x = ((x - 50) * 16 / 100)  # Adjusted for 100x100 grid
        scene_y = ((y - 50) * 16 / 100)  # Adjusted for 100x100 grid
        return scene_x, scene_y, 0

class Item:
    def __init__(self, scene, color, position):
        self.scene = scene
        grid_space_scale = 0.1
        self.item = Circle(color=color).scale(3*grid_space_scale)
        self.item.move_to(self._grid_to_scene_coords(position))
        self.being_held = False
        self.position = position

    def move_to(self, new_position):
        self.position = new_position
        self.item.move_to(new_position)
        

    def _grid_to_scene_coords(self, point):
        x, y = point
        scene_x = ((x - 50) * 16 / 100)  # Adjusted for 100x100 grid
        scene_y = ((y - 50) * 16 / 100)  # Adjusted for 100x100 grid
        return scene_x, scene_y, 0

class RobotScene(Scene):
    def setup_scene(self):
        grid = NumberPlane(
            x_range=[0, 100, 5], 
            y_range=[0, 100, 5],  
            x_length=16,
            y_length=16,
            background_line_style={"stroke_color": BLACK, "stroke_width": 1}
        )
        self.add(grid)

        self.bot = Bot(self, BLUE, (50, 50)) 
        self.add(self.bot.box)

    def construct(self):
        self.setup_scene()
        
class AIScene(RobotScene):
    def construct(self):
        super().construct() 

        item = Item(self, color=GREEN, position=(20, 50))
        self.add(item.item)
        
        self.bot.pick_up_item(item)
        
        self.bot.move(10, (-1, 0), 10)
        
        self.bot.place_item((80, 50))


AIScene2 = AIScene()
AIScene2.render()