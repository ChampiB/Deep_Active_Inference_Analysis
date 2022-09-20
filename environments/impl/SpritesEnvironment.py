import collections
import os
from git import Repo
import numpy as np
import random
import gym
from gym import spaces
import pygame
from gui.AnalysisConfig import AnalysisConfig

dSpritesDataset = collections.namedtuple('dSpritesDataset', field_names=['images', 'latent_states', 's_sizes'])


#
# This file contains the code of the dSprites environment adapted from:
# https://github.com/zfountas/deep-active-inference-mc/blob/master/src/game_environment.py
#
# Additionally, when the shape reaches top border of the image a hint describing where to bring the shape
# to get high reward is displayed
#
# TODO Unify epistemic and standard dsprites
class SpritesEnvironment(gym.Env):

    def __init__(self, json):
        """
        Constructor (compatible with OpenAI gym environment)
        :param json: a json object describing the environment configuration
        """
        # Gym compatibility
        super(SpritesEnvironment, self).__init__()
        self.np_precision = np.float64
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(low=0, high=255, shape=(64, 64, 1), dtype=self.np_precision)

        # Small dataset attributes
        self.n_elements_small_ds = 50
        self.group_size = 1024

        # Clone the repository if it does not exist
        conf = AnalysisConfig.instance
        dataset_dir = conf.datasets_directory + "dsprites-dataset/"
        first_time = False
        if not os.path.isdir(dataset_dir):
            Repo.clone_from("https://github.com/deepmind/dsprites-dataset.git", dataset_dir)
            first_time = True
        self.images, self.latent_states, self.s_sizes = self.load_sprites_dataset(
            dataset_dir, split_dataset=first_time
        )

        # Initialize fields
        self.repeats = int(json["n_repeats"])
        self.difficulty = json["difficulty"].lower()
        self.max_trial_length = int(json["max_trial_length"])
        self.epistemic = (json["epistemic"].lower() == "true")

        # Epistemic task attributes
        self.reward_on_the_right = True
        self.display_reward_hint = False

        # General task attributes
        self.state = np.zeros_like(self.latent_states[0], dtype=self.np_precision)
        self.index = 0
        self.last_r = 0.0
        self.frame_id = 0
        self.reset()

    def load_sprites_dataset(self, ds_dir, split_dataset):
        """
        Load the disentanglement testing sprites' dataset
        :param ds_dir: the path to the directory containing the dataset
        :param split_dataset: whether the dataset must be split for faster reloading
        :return: the dataset
        """
        if split_dataset:
            # Load large dataset
            ds_file = "dsprites_ndarray_co1sh3sc6or40x32y32_64x64.npz"
            dataset = np.load(ds_dir + ds_file, allow_pickle=True, encoding='latin1')
            images = dataset['imgs'].reshape(-1, 64, 64, 1)
            metadata = dataset['metadata'][()]
            s_sizes = metadata['latents_sizes']  # [1 3 6 40 32 32]
            s_bases = np.concatenate((metadata['latents_sizes'][::-1].cumprod()[::-1][1:], np.array([1, ])))
            s_bases = np.squeeze(s_bases)  # self.s_bases = [737280 245760 40960 1024 32 1]

            # Take a random sample from large dataset
            indices = np.random.randint(images.shape[0] / self.group_size, size=self.n_elements_small_ds)
            all_images = []
            all_latent_states = []
            for index in indices:
                # Get images
                img = images[index * self.group_size: (index + 1) * self.group_size]
                all_images.append(img)

                # Get latent states
                latent_state = self.to_multi_index(index * self.group_size, s_bases)
                latent_states = []
                for x in range(0, s_sizes[4]):
                    latent_state[5] = 0
                    for y in range(0, s_sizes[5]):
                        latent_states.append(latent_state.copy())
                        latent_state[5] += 1
                    latent_state[4] += 1
                all_latent_states.append(latent_states)

            # Concatenate all images and latent states
            all_images = np.concatenate(all_images, axis=0)
            all_latent_states = np.concatenate(all_latent_states, axis=0)

            # Save the random sample
            np.savez(
                ds_dir + "ds-sprites.npz", images=all_images, latent_states=all_latent_states, s_sizes=s_sizes
            )

            return dSpritesDataset(all_images, all_latent_states, s_sizes)

        # Load small dataset
        dataset = np.load(ds_dir + "ds-sprites.npz", allow_pickle=True, encoding='latin1')
        return dSpritesDataset(dataset["images"], dataset["latent_states"], dataset["s_sizes"])

    @staticmethod
    def to_multi_index(index, bases):
        """
        Compute the multi-index from the index and bases
        :param index: the index
        :param bases: the base
        :return: the multi-index
        """
        multi_index = []
        i = 0
        while i <= bases.shape[0] - 1:
            multi_index.append(int(index / bases[i]))
            index %= bases[i]
            i += 1
        return multi_index

    @staticmethod
    def get_keys_to_action():
        """
        Getter
        :return: a dictionary mapping kwy to action
        """
        return {None: 4, pygame.K_s: 0, pygame.K_w: 1, pygame.K_a: 2, pygame.K_d: 3}

    def reset(self):
        """
        Reset the state of the environment to an initial state
        :return: the first observation
        """
        self.index = np.random.randint(len(self.latent_states))
        self.state = self.latent_states[self.index].copy()
        print(f"reset: index[{self.index % 1024}], state{self.state}")
        self.last_r = 0.0
        self.frame_id = 0
        self.reward_on_the_right = bool(random.getrandbits(1))
        self.display_reward_hint = False
        return self.current_frame()

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
        if action != 4:
            print(f"state: {self.state}, index: {self.index % 1024}, action: {action}")
        for i in range(self.repeats):
            if action < 0 or action > 4:
                exit('Invalid action.')
            done = actions_fn[action]()
            if self.difficulty == "easy" and self.epistemic is False:
                done, self.last_r = self.compute_easy_reward()
            if done:
                if action != 4:
                    print(f"state: {self.state}, index: {self.index % 1024}")
                    print()
                return self.current_frame(), self.last_r, True, {}
        if action != 4:
            print(f"state: {self.state}, index: {self.index % 1024}")
            print()

        # Make sure the environment is reset if the maximum number of steps in the trial has been reached.
        if self.frame_id >= self.max_trial_length:
            return self.current_frame(), -1.0, True, {}
        else:
            return self.current_frame(), self.last_r, False, {}

    def current_frame(self):
        """
        Return the current frame (i.e. the current observation)
        :return: the current observation
        """
        image = self.images[self.index].astype(self.np_precision)
        image = np.repeat(image, 3, 2) * 255.0
        if self.epistemic is True and self.display_reward_hint:
            if self.reward_on_the_right:
                image[:, 58:64, 0] = 255.0
            else:
                image[:, 0:6, 0] = 255.0
        return image

    #
    # Actions
    #

    def down(self):
        """
        Execute the action "down" in the environment
        :return: true if the object crossed the bottom line
        """
        # If y position is less than zero, reset it to zero
        if self.y_pos < 0:
            self.y_pos = 0

        # Update y coordinate
        self.y_pos += 1.0
        if self.y_pos <= 31:
            self.index += 1

        # If the object cross the bottom line, the difficulty is hard, and the epistemic task is disabled
        if self.y_pos >= 32 and self.difficulty == "hard" and self.epistemic is False:
            self.last_r = self.compute_hard_reward()
            return True

        # If the object cross the bottom line, the difficulty is hard, and the epistemic task is enabled
        if self.y_pos >= 32 and self.difficulty == "hard" and self.epistemic is True:
            self.last_r = self.compute_hard_reward_epistemic()
            return True
        return False

    def up(self):
        """
        Execute the action "up" in the environment
        :return: false (the object never cross the bottom line when moving up)
        """
        # If y position more than 31, reset it to 31
        if self.y_pos > 31:
            self.y_pos = 31

        # Update y position
        self.y_pos -= 1.0
        if self.y_pos >= 0:
            self.index -= 1

        # Display hint if required
        if self.y_pos <= 0:
            self.display_reward_hint = True

        return False

    def right(self):
        """
        Execute the action "right" in the environment
        :return: false (the object never cross the bottom line when moving left)
        """
        # If x position is negative, reset it to zero
        if self.x_pos < 0:
            self.x_pos = 0

        # Update x position
        self.x_pos += 1.0
        if self.x_pos <= 31:
            self.index += 32

        # Compute reward
        if self.x_pos >= 32 and self.difficulty == "easy" and self.epistemic is True:
            self.last_r = 1 if self.reward_on_the_right else -1
            return True

        return False

    def left(self):
        """
        Execute the action "left" in the environment
        :return: false (the object never cross the bottom line when moving right)
        """
        if self.x_pos > 31:
            self.x_pos = 31

        self.x_pos -= 1.0
        if self.x_pos >= 0:
            self.index -= 32

        if self.x_pos < 0 and self.difficulty == "easy" and self.epistemic is True:
            self.last_r = 1 if not self.reward_on_the_right else -1
            return True

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
        if self.x_pos > 15:
            return float(15.0 - self.x_pos) / 16.0
        else:
            return float(16.0 - self.x_pos) / 16.0

    def compute_reward_on_the_right(self):
        """
        Compute the obtained by the agent when an ellipse or heart crosses the bottom wall
        :return: the reward
        """
        if self.x_pos > 15:
            return float(self.x_pos - 15.0) / 16.0
        else:
            return float(self.x_pos - 16.0) / 16.0

    def compute_hard_reward_epistemic(self):
        """
        Compute the reward obtained by the agent if the environment difficulty is hard
        :return: the reward
        """
        # Ensure that the current position is valid
        self.ensure_position_is_valid()

        # If the object crossed the bottom line, then: compute the reward, generate a new image and return true.
        if self.reward_on_the_right:
            return self.compute_reward_on_the_right()
        else:
            return self.compute_reward_on_the_left()

    def compute_hard_reward(self):
        """
        Compute the reward obtained by the agent if the environment difficulty is hard.
        :return: the reward.
        """
        # Ensure that the current position is valid
        self.ensure_position_is_valid()

        # If the object crossed the bottom line, then: compute the reward, generate a new image and return true.
        if self.state[1] < 0.5:
            return self.compute_reward_on_the_left()
        else:
            return self.compute_reward_on_the_right()

    def compute_easy_reward(self):
        """
        Compute the reward obtained by the agent if the environment difficulty is easy.
        :return: whether the trial has ended, and the reward.
        """
        # Ensure that the current position is valid
        self.ensure_position_is_valid()

        # Compute reward
        tx, ty = (0, 31) if self.state[1] < 0.5 else (31, 31)
        reward = -1.0 + (62 - abs(tx - self.x_pos) - abs(ty - self.y_pos)) / 31.0
        return self.x_pos == tx and self.y_pos == ty, reward

    def ensure_position_is_valid(self):
        """
        Ensure that the current position is valid
        """
        # Make sure x position is valid
        if self.x_pos < 0:
            self.x_pos = 0
        if self.x_pos > 31:
            self.x_pos = 31

        # Make sure y position is valid
        if self.y_pos < 0:
            self.y_pos = 0
        if self.y_pos > 31:
            self.y_pos = 31

    #
    # Getter and setter.
    #

    @property
    def y_pos(self):
        """
        Getter
        :return: the current position of the object on the y-axis
        """
        return self.state[5]

    @y_pos.setter
    def y_pos(self, new_value):
        """
        Setter
        :param new_value: the new position of the object on the y-axis
        :return: nothing
        """
        self.state[5] = new_value

    @property
    def x_pos(self):
        """
        Getter
        :return: the current position of the object on the x-axis
        """
        return self.state[4]

    @x_pos.setter
    def x_pos(self, new_value):
        """
        Setter
        :param new_value: the new position of the object on the x-axis
        :return: nothing
        """
        self.state[4] = new_value
