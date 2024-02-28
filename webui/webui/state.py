import os
import reflex as rx
from dotenv import load_dotenv
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema import BaseOutputParser
import shutil
import time
from webui.grid_scene import *
from webui.template import template, path
from langchain_community.chat_models import BedrockChat
from langchain_openai import ChatOpenAI
import boto3
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback
import random
import subprocess

import os
import aiofiles
import asyncio
from concurrent.futures import ThreadPoolExecutor
import random

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")


grid = '''
from manim import Scene, Square, Circle, BLUE, RED, GREEN, MoveAlongPath, Line, NumberPlane, BLACK, config, WHITE, AnimationGroup, ApplyMethod, UP, DOWN, LEFT, Rectangle, Text

config.pixel_height = 480
config.pixel_width = 480
config.frame_height = 16.0
config.frame_width = 16.0
config.background_color = WHITE
config.frame_rate = 15
config.disable_caching = True

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
            self.scene.wait(1)
        else:
            self.scene.play(bot_move_animation)
            self.scene.wait(1)
    
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


# AIScene2 = AIScene()
# AIScene2.render()

'''


class CodeParser(BaseOutputParser):
    def parse(self, text: str):
        return text.strip().split("```")


def format_history(chats):
    formatted_messages = []
    for chat in chats:
        question = "User: " + str(chat.question)
        answer = "Assistant: " + str(chat.answer)
        formatted_messages.extend((question, answer))
    return formatted_messages


human_template = "Prompt: {text}"

client = boto3.client("bedrock-runtime")

model = ChatOpenAI(model = 'gpt-3.5-turbo', openai_api_key = api_key)

#model = BedrockChat(model_id="meta.llama2-70b-chat-v1")


class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str


class ImageURL:
    def __init__(self):
        self.file_version = 0
        self.filename = "AIScene_0.mp4"
        self.fileaddr = "/" + self.filename

    def update_file(self):
        self.file_version += 1
        self.filename = f"AIScene_{self.file_version}.mp4"
        self.fileaddr = "/" + self.filename


img = ImageURL()

DEFAULT_CHATS = {
    "Demo": [],
}


def add_br_tags(input_string):
    lines = input_string.split("\n")

    lines_with_br = [line + "<br>" for line in lines]

    return "\n".join(lines_with_br)


class State(rx.State):
    """The app state."""

    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, list[QA]] = DEFAULT_CHATS

    # The current chat name.
    current_chat = "Demo"

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    video_processing: bool = False

    # The name of the new chat.
    new_chat_name: str = ""

    # Whether the drawer is open.
    drawer_open: bool = False

    modal_open: bool = False

    url_index: int = 0

    url_list: list = []

    url: str = ""
    
    session: int = None
    
    auth_token: str = rx.Cookie()

    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

        # Toggle the modal.
        self.modal_open = False

    def update_url(self, new_url: str):
        self.url_list.append(new_url)
        self.url_index += 1
        self.url = new_url

    def toggle_modal(self):
        """Toggle the new chat modal."""
        self.modal_open = not self.modal_open

    def toggle_drawer(self):
        """Toggle the drawer."""
        self.drawer_open = not self.drawer_open

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]
        self.toggle_drawer()

    def set_chat(self, chat_name: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        self.current_chat = chat_name
        self.toggle_drawer()

    @rx.var
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list(self.chats.keys())

    async def process_question(self, form_data: dict[str, str]):
        img.update_file()
        # Get the question from the form
        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return

        model = self.openai_process_question

        async for value in model(question):
            yield value

    async def openai_process_question(self, question: str):
        """Get the response from the API asynchronously.

        Args:
            question: A string containing the question.
        """
        
        start_time = time.time()
        worked = True

        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)
        self.video_processing = True
        self.processing = True
        yield
        await asyncio.sleep(0)  # Yield control to the event loop

        history_messages = format_history(self.chats[self.current_chat])

        final_template = history_messages
        final_template.insert(0, ("system", template))
        final_template.append(("human", human_template))

        prompt = ChatPromptTemplate.from_messages(final_template)
        messages = prompt.format_messages(text=question)

        loop = asyncio.get_running_loop()

        # Wrap the synchronous model.invoke call to run it in a thread pool
        result = await loop.run_in_executor(None, lambda: model.invoke(messages))
        parsed = CodeParser().parse(result.content)

        try:
            reason = parsed[0]
            code = parsed[1]

            exec_code = code.replace("python", "").strip()

            exec_code = (
                "config.output_dir = 'assets'\n"
                + exec_code
                + "\nAIScene2 = AIScene() \nAIScene2.render()"
            )

            await self.generate_video(exec_code)

        except Exception as e:
            print(parsed)
            error_text = traceback.format_exc()
            print(error_text)
            answer_text = "Sorry, an error occurred: " + str(e)
            self.chats[self.current_chat][-1].answer += answer_text
            self.chats = self.chats
            worked = False

        if worked:
            answer_text = add_br_tags(reason)

            self.chats[self.current_chat][-1].answer += answer_text
            self.chats = self.chats

            answer_text = rf"""
```python3
{code}
```
"""
            self.chats[self.current_chat][-1].answer += answer_text
            self.chats = self.chats
        
        end_time = time.time()  # Capture end time after processing is complete
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")

        self.processing = False

    # async def generate_video(self, exec_code):
        
    #     session = random.randint(1000000000, 9999999999)
        
    #     self.video_processing = True
    #     loop = asyncio.get_running_loop()

    #     # Define a synchronous wrapper function that will execute the code
    #     def execute_code():
    #         # This is where your synchronous code execution happens
    #         exec(exec_code, globals())

    #     # Run the synchronous function in a separate thread
    #     await loop.run_in_executor(ThreadPoolExecutor(), execute_code)
    #     await asyncio.sleep(0.1)  # 100ms delay after executing the code

    #     # Proceed with moving the file
    #     source_path = f"{path}/media/videos/480p15/AIScene.mp4"
    #     destination_dir = f"{path}/assets/{session}"
    #     destination_path = os.path.join(destination_dir, img.filename)
    #     shutil.copy(source_path, destination_path)
        
    #     await asyncio.sleep(0.1)  # 100ms delay after copying the file

    #     # Consider replacing time.sleep with asyncio.sleep for async sleep
    #     await asyncio.sleep(1.5)  # Async sleep before updating the URL
    #     self.update_url(img.fileaddr)
    #     self.video_processing = False
    
    
    def check_login(self):
        if self.auth_token:
            # User is logged in
            pass
        else:
            print('hi')

        
        
    # async def async_copy(self, source_path, destination_dir, img_filename):
    #     # Ensure the destination directory exists
    #     os.makedirs(destination_dir, exist_ok=True)
        
    #     destination_path = os.path.join(destination_dir, img_filename)
        
    #     # Open the source file and destination file asynchronously
    #     async with aiofiles.open(source_path, 'rb') as src, aiofiles.open(destination_path, 'wb') as dst:
    #         # Read and write in chunks to avoid loading the whole file into memory
    #         while True:
    #             data = await src.read(64 * 1024)  # Read in chunks of 64KB
    #             if not data:
    #                 break  # End of file reached
    #             await dst.write(data)
                
    async def generate_video(self, exec_code):
        
        self.session = random.randint(1000000000, 9999999999)
        
        self.video_processing = True
        loop = asyncio.get_running_loop()
        config.output_file
        
        if not os.path.exists(f'/home/ubuntu/robot-animation-ai/webui/temp/{self.session}'):
            os.makedirs(f'/home/ubuntu/robot-animation-ai/webui/temp/{self.session}')
        if not os.path.exists(f'/home/ubuntu/robot-animation-ai/webui/assets/{self.session}'):
            os.makedirs(f'/home/ubuntu/robot-animation-ai/webui/assets/{self.session}')
        
        save = f'config.media_dir = "/home/ubuntu/robot-animation-ai/webui/temp/{self.session}" \nconfig.output_file = "/home/ubuntu/robot-animation-ai/webui/assets/{self.session}/AIScene.mp4"\n'

        
        exec_code = save + exec_code

        # Define a synchronous wrapper function that will execute the code
        def execute_code():
            # This is where your synchronous code execution happens
            exec(exec_code, globals())

        # Run the synchronous function in a separate thread
        await loop.run_in_executor(ThreadPoolExecutor(), execute_code)
        await asyncio.sleep(0.1)  # 100ms delay after executing the code

        # Async sleep before updating the URL
        time.sleep(2)
        self.update_url(f'/{self.session}/AIScene.mp4') 
        print(self.url)
        self.video_processing = False
        
        directory_path = f"/home/ubuntu/robot-animation-ai/webui/temp/{self.session}"
        
        if os.path.exists(directory_path):
            print('deleted folder')
            shutil.rmtree(directory_path)
