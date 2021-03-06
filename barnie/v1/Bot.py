import hlt
import logging
import os
import time
import numpy as np
from scipy import stats
import random
from v1.GameState import GameState
from v1.ShipState import ShipState
from v1.NeuralNet2 import NeuralNetwork
from v1.Strategy import *

VERSION = 1

game = hlt.Game("barnie")
# Then we print our start message to the logs
logging.info("Starting Barnie!")


class Bot:
    def __init__(self, name, nn_weights=None):
        # current_directory = os.path.dirname(os.path.abspath(__file__))
        self.nn_weights = 2*np.random.rand(200)-1
        if nn_weights is not None:
            self.nn_weights = nn_weights

        self._name = name


        logging.info(str("Iteration :   ") + self._name)
        # with open("counter.dat", "a+") as f:
        #     self.val = int(f.read() or 0) + 1
        #     f.seek(0)
        #     f.truncate()
        #     f.write(str(self.val))

        # Neural Network
        self.nn_layer = np.array([NUM_INPUTS, 10, NUM_OUTPUTS])
        self.nn = NeuralNetwork(self.nn_layer, self.nn_weights)


    def play(self):
        logging.info("Started playing")

        with open("weight{}.vec".format(self._name), "a") as f:

            f.write(str(self.nn.W1) + str(self.nn.W2))
            f.write('\n')

        while True:
            start_time = time.time()
            game_map = game.update_map()
            logging.info("Reading game_map")
            commands = []
            game_state = GameState(game_map)

            for ship in game_map.get_me().all_ships():
                if ship.docking_status is not ship.DockingStatus.UNDOCKED:
                    continue

                ship_state = ShipState(game_map, game_state, ship)
                nn_input = np.append(game_state.values, ship_state.values)
                #logging.info(str(nn_input))
                nn_out = self.nn.forward(nn_input)

                action = np.argmax(nn_out)
                logging.info("Action = " + str(action))

                new_command = self.ship_command(game_map, ship, ship_state, action)
                if new_command:
                    commands.append(new_command)

                #game.send_command_queue(commands)

                with open("input.vec".format(VERSION), "a") as f:
                    f.write(str([round(item, 3) for item in nn_input]))
                    f.write('\n')

                with open("nn_output{}.vec".format(self._name), "a") as f:
                    f.write(str(nn_out))
                    f.write('\n')
            game.send_command_queue(commands)

    def ship_command(self, game_map, ship, ship_state, action):
        new_command = ''
        if action is 0:
            '''Attack closest enemy ship'''
            target = ship_state.get_closest_enemy_ship()
            new_command = ship.navigate(
                ship.closest_point_to(target),
                game_map, speed=int(hlt.constants.MAX_SPEED), ignore_ships=False)

        elif action is 1 or 2:
            '''Dock and mine closest owned/neutral planet'''
            target = ship_state.get_closest_available_planet()
            if target.is_full():
                # Go attack if the planet is full
                new_command = self.ship_command(game_map, ship, ship_state, 0)
            elif ship.docking_status is ship.DockingStatus.UNDOCKED:
                if ship.can_dock(target):
                    new_command = ship.dock(target)
                else:
                    new_command = ship.navigate(
                        ship.closest_point_to(target),
                        game_map, speed=int(hlt.constants.MAX_SPEED), ignore_ships=False)


        #logging.info("Ship " + str(ship.id) + " does action " + str(action))
        return new_command
