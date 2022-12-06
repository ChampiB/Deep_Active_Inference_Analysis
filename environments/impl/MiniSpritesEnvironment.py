import numpy as np
import random
import gym
from gym import spaces
import pygame


#
# This file contains the code of the dSprites environment adapted from:
# https://github.com/zfountas/deep-active-inference-mc/blob/master/src/game_environment.py
#
# Additionally, when the shape reaches top border of the image a hint describing where to bring the shape
# to get high reward is displayed
#
class MiniSpritesEnvironment(gym.Env):

    def __init__(self, json):
        """
        Constructor (compatible with OpenAI gym environment)
        :param json: a json object describing the environment configuration
        """
        # Gym compatibility
        super(MiniSpritesEnvironment, self).__init__()
        self.np_precision = np.float64
        self.action_space = spaces.Discrete(5)
        self.observation_space = spaces.Box(low=0, high=255, shape=(64, 64, 1), dtype=self.np_precision)

        # Initialize fields
        self.width = int(json["width"])
        self.height = int(json["height"])
        self.max_trial_length = int(json["max_trial_length"])
        self.w2 = self.width / 2
        self.w21 = (self.width / 2) - 1

        # Environment state
        self.reward_on_the_right = bool(random.getrandbits(1))
        self.x = random.randint(0, self.width)
        self.y = random.randint(0, self.height)

        # Attributes used for the creation of A, B, C, and D matrices
        self.state_names = ["S_x", "S_y", "S_color"]
        self.s_sizes = [self.width, self.height, 2]

        # General task attributes
        self.last_r = 0.0
        self.frame_id = 0
        self.reset()

    def render(self, mode="human"):
        """
        Renter the environment
        :param mode: the mode of display to use
        :return: the current frame
        """
        if mode != "rgb_array":
            raise NotImplementedError()
        return self.current_frame()

    def get_state(self):
        """
        Getter
        :return: a vector representing the environment state, [x position, y position, dot color]
        """
        return np.array([self.x, self.y, self.reward_on_the_right])

    def reset(self):
        """
        Reset the state of the environment to an initial state
        :return: the first observation
        """
        self.last_r = 0.0
        self.frame_id = 0
        self.reward_on_the_right = bool(random.getrandbits(1))
        self.x = random.randint(0, self.width - 1)
        self.y = random.randint(0, self.height - 1)
        return self.current_frame()

    @staticmethod
    def get_keys_to_action():
        """
        Getter
        :return: a dictionary mapping kwy to action
        """
        return {None: 4, pygame.K_s: 0, pygame.K_w: 1, pygame.K_a: 2, pygame.K_d: 3}

    def current_frame(self):
        """
        Return the current frame (i.e. the current observation)
        :return: the current observation
        """
        self.ensure_position_is_valid()
        self.x = int(self.x)
        self.y = int(self.y)
        image = np.zeros([self.height, self.width, 3])
        for x in range(self.width):
            for y in range(self.height):
                if self.x == x and self.y == y:
                    image[y][x][0 if self.reward_on_the_right else 1] = 255
        return image

    def step(self, action):
        """
        Execute one time step within the environment
        :param action: the action to perform
        :return: next observation, reward, is the trial done?, information
        """
        # Increase the frame index, that count the number of frames since the beginning of the episode.
        self.frame_id += 1

        # Simulate the action requested by the user.
        actions_fn = [self.down, self.up, self.left, self.right, self.idle]
        if not isinstance(action, int):
            action = action.item()
        if action < 0 or action > 4:
            exit('Invalid action.')
        done = actions_fn[action]()
        if done:
            return self.current_frame(), self.last_r, True, {}

        # Make sure the environment is reset if the maximum number of steps in the trial has been reached.
        if self.frame_id >= self.max_trial_length:
            return self.current_frame(), -1.0, True, {}
        else:
            return self.current_frame(), self.last_r, False, {}

    #
    # Actions
    #
    def down(self):
        """
        Execute the action "down" in the environment
        :return: true if the object crossed the bottom line
        """
        # If y position is less than zero, reset it to zero
        if self.y < 0:
            self.y = 0

        # Update y coordinate
        self.y += 1.0

        # If the object cross the bottom line, the difficulty is hard, and the epistemic task is disabled
        if self.y >= self.height:
            self.last_r = self.compute_hard_reward()
            return True
        return False

    def up(self):
        """
        Execute the action "up" in the environment
        :return: false (the object never cross the bottom line when moving up)
        """
        # If y position more than 31, reset it to 31
        if self.y > self.height - 1:
            self.y = self.height - 1

        # Update y position
        self.y -= 1.0
        return False

    def right(self):
        """
        Execute the action "right" in the environment
        :return: false (the object never cross the bottom line when moving left)
        """
        # Check if the shape can move
        if self.y >= self.height:
            return False

        # If x position is negative, reset it to zero
        if self.x < 0:
            self.x = 0

        # Update x position
        self.x += 1.0
        return False

    def left(self):
        """
        Execute the action "left" in the environment
        :return: false (the object never cross the bottom line when moving right)
        """
        # Check if the shape can move
        if self.y >= self.height:
            return False

        # If x position is too big, reset it to its maximum value
        if self.x > self.width - 1:
            self.x = self.width - 1

        # Update x position
        self.x -= 1.0
        return False

    @staticmethod
    def idle():
        """
        Execute the action "idle" in the environment
        :return: false
        """
        return False

    #
    # Reward computation
    #
    def compute_reward_on_the_left(self):
        """
        Compute the obtained by the agent when a square crosses the bottom wall
        :return: the reward
        """
        if self.x > self.w21:
            return float(self.w21 - self.x) / self.w2
        else:
            return float(self.w2 - self.x) / self.w2

    def compute_reward_on_the_right(self):
        """
        Compute the obtained by the agent when an ellipse or heart crosses the bottom wall
        :return: the reward
        """
        if self.x > self.w21:
            return float(self.x - self.w21) / self.w2
        else:
            return float(self.x - self.w2) / self.w2

    def compute_hard_reward(self):
        """
        Compute the reward obtained by the agent if the environment difficulty is hard.
        :return: the reward.
        """
        # Ensure that the current position is valid
        self.ensure_position_is_valid()

        # If the object crossed the bottom line, then: compute the reward, generate a new image and return true.
        if self.reward_on_the_right:
            return self.compute_reward_on_the_right()
        else:
            return self.compute_reward_on_the_left()

    def ensure_position_is_valid(self):
        """
        Ensure that the current position is valid
        """
        # Make sure x position is valid
        if self.x < 0:
            self.x = 0
        if self.x > self.width - 1:
            self.x = self.width - 1

        # Make sure y position is valid
        if self.y < 0:
            self.y = 0
        if self.y > self.height - 1:
            self.y = self.height - 1
