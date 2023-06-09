import os
from typing import Any, Tuple
import numpy as np
import math
import random


def fitness_function(max_position, num_wheels, total_chassis_volume, total_wheels_volume, frames) -> float:
    return (
            (max_position * 3) ** 3.5 -
            (num_wheels ** 5) -
            ((total_chassis_volume * 5) ** 3) -
            ((total_wheels_volume * 10) ** 5) -
            frames
    )


def fitness_function2(
    max_position, is_winner, num_wheels, min_num_wheels, max_contacts_penalty,
    contacts_threshold, wheels_contacts, frames, chassis_volume, chassis_mass,
    wheels_volume, wheels_mass, cumulative_stall_time
) -> float:
    return fitness_scale_function(
        10 * max_position -  # 10e4
        # 1000 * is_winner -  # 10e3
        # 50 * num_wheels -  # 10e2
        50 * num_wheels if num_wheels > min_num_wheels else 0 -  # 10e2
        np.sum(
            [
                (-max_contacts_penalty/contacts_threshold) * contacts + max_contacts_penalty
                if contacts <= contacts_threshold else 0
                for contacts in wheels_contacts
            ]
        ) -  # 10e2
        (1 / (is_winner + 0.10)) * (frames / 100) -  # 10e2
        chassis_mass -  # 10e2
        100 * chassis_volume -  # 10e2
        wheels_mass / 10 -  # 10e2
        10 * wheels_volume -  # 10e2
        10 * cumulative_stall_time  # 10e2 (massimo 10e5)
    )


# Settings that control everything.
settings = {}
settings['boxcar'] = {}
settings['ga'] = {}
__settings_cache = {}
# The settings specific to the boxcar
settings['boxcar'] = {
    ### Floor ###
    'floor_tile_height': (.15, float),  # .15
    'floor_tile_width': (1, float),  # 1.5
    'max_floor_tiles': (150, int),
    'gaussian_floor_seed': (random.randint(1, 1000), int),

    # MN MODIFIED if the tiles are strange or not
    'min_num_section_per_tile': (1, int),  # MN MODIFIED min number of sections per tile
    'max_num_section_per_tile': (1, int),  # MN MODIFIED max number of sections per tile
    
    # Type of floor : 'gaussian', 'ramp', 'jagged', 'holes', 'walls' , 'flat'
    'floor_creation_type': ('gaussian', str),
    ### Floor - Gaussian random. Used when 'floor_creation_type' == 'gaussian' ###
    # Only needed if using gaussian random floor creation
    'tile_angle_mu': (8, float),
    'tile_angle_std': (15, float),
    'tile_gaussian_denominator': (10, float),
    'tile_gaussian_threshold': (10, int),

    ### Floor - ramp. Used when 'floor_creation_type' == 'ramp' ###
    # Only needed if using ramp floor creation
    # If 'ramp_constant_angle' is defined, it will use the constant ramp
    'ramp_constant_angle': (None, (float, type(None))),
    'ramp_constant_distance': (None, (float, type(None))),

    # If 'ramp_constant_angle' is not defined, it will use an increasing ramp
    'ramp_increasing_angle': (1.2, (float, type(None))),
    'ramp_start_angle': (1, (float, type(None))),
    'ramp_increasing_type': ('multiply', (str, type(None))),
    'ramp_max_angle': (55, float),

    'ramp_approach_distance': (10, float),
    'ramp_distance_needed_to_jump': (10, float),

    ### Floor - holes. 
    'number_of_holes': (5, int),  # MN MODIFIED number of holes
    'hole_distance_needed_to_jump': (1, float),  # MN MODIFIED the first jump distance
    'incremental_distance': (1, float),  # MN MODIFIED the distance incrementation for each jump 0 = no incrementation

    ### Floor - wall. 
    'number_of_walls': (5, int), # MN MODIFIED number of walls
    'number_of_wall_tiles': (1, int), # MN MODIFIED number of tiles per wall
    'wall_tile_incremental': (1, int),  # MN MODIFIED the tile incrementation for each wall 0 = no incrementation

    ### Jagged - ramp. Used when 'floor_creation_type' == 'jagged' ###
    # Only needed if using jaged floor creation
    'jagged_increasing_angle': (45, float),
    'jagged_decreasing_angle': (45, float),

    # Car
    'car_max_tries': (20, int),

    # Chassis
    'min_chassis_axis': (0.1, float),
    'max_chassis_axis': (1.3, float),
    'min_chassis_density': (30.0, float),
    'max_chassis_density': (300.0, float),

    # Wheel
    'min_wheel_density': (40.0, float),
    'max_wheel_density': (200.0, float),
    'min_num_wheels': (2, int),
    'max_num_wheels': (7, int),
    'min_wheel_radius': (0.1, float),
    'max_wheel_radius': (0.5, float),

    "min_wheel_vertices_radius": (0.1, float),
    "max_wheel_vertices_radius": (1.3, float),

    "circle_wheel_probability": (0.5, float),

    "min_num_wheels_vertices": (3, int),
    "max_num_wheels_vertices": (8, int),

    "round_length_vertices_coordinates": (6, int),

    # World
    'gravity': ((0, -9.8), tuple),  # X/Y direction

    # Display
    'show': (True, bool),  # Whether or not to display anything
    'fps': (45, int),
    'run_at_a_time': (50, int),
    'should_smooth_camera_to_leader': (False, bool),
    'show_label': (True, bool),  # MN MODIFIED show label of the car or not

    "population_headers": (
        "generation," +
        "id," +
        "fitness," +
        "max_position," +
        "chassis_mass," +
        ",".join([f"wheels_mass_{i}" for i in range(0, 8)]) + 
        "," +
        "frames," +
        "is_winner," +
        "cumulative_stall_time," +
        ",".join([f"chassis_vertices_x_{i}" for i in range(0, 8)]) +
        "," +
        ",".join([f"chassis_vertices_y_{i}" for i in range(0, 8)]) +
        "," +
        ",".join([f"chassis_densities_{i}" for i in range(0, 8)]) +
        "," +
        ",".join([f"wheel_radii_{i}" for i in range(0, 8)]) +
        "," +
        ",".join([f"wheel_densities_{i}" for i in range(0, 8)]) +
        "," +
        ",".join([f"wheels_vertices_r_{i}" for i in range(0, 8)]) +
        "," +
        ",".join([f"wheels_vertices_theta_{i}" for i in range(0, 8)]) +
        "\n",
        # "chassis_vertices_x, chassis_vertices_y, chassis_densities, wheel_radii, wheel_densities, wheels_vertices_r, wheels_vertices_theta\n",
        str
    )
}

# Genetic algorithm specific settings
settings['ga'] = {
    "max_generations": (10, int),

    "min_fitness_value": (1e-10, float),

    # Selection
    'num_parents': (50, int),
    'num_offspring': (50, int),

    'elitism': (0.05, float),

    'selection_type': ('plus', str),
    'lifespan': (5, float),

    # Mutation
    'mutation_rate': (0.5, float),
    'gaussian_mutation_scale': (0.2, float),
    'mutation_rate_type': ('static', str),

    # Crossover
    'crossover_probability': (0.5, float), # Single point binary crossover probability
    'SBX_eta': (1, float),
    'crossover_selection': ('tournament', str), 
    'tournament_size': (5, int),

    "max_contacts_penalty": (50, int),
    "contacts_threshold": (10, int),

    # Fitness function
    "fitness_function": (fitness_function, any),
    "fitness_function2": (fitness_function2, any)
}

settings['window'] = {
    'width': (1920, int),
    'height': (1080, int)
}


def fitness_scale_function(x: float) -> float:
    return (math.atan(x) + math.pi/2) if x <= 0 else (math.pow(x, (3/4)) + math.pi/2)


def _verify_constants() -> None:
    failed = []

    for controller in settings:
        setting_map = settings[controller]
        for constant in setting_map:
            try:
                _get_constant(constant, controller)
            except:
                failed.append('{}: {}'.format(controller, constant))

    if failed:
        failed_constants = '\n'.join(fail for fail in failed)
        raise Exception('The following constants have invalid values for their types:\n{}'.format(failed_constants))


def _get_constant(constant: str, controller: str) -> Any:
    """
    Get the end value represented by the constant you are searching for
    """
    # Caches are good. Normally making a cache for a dictionary doesn't make sense.
    # Since I allow dependencies on other variables, a lookup could be O(N). By adding
    # a cache where (constant, controller) is the key, we get O(1) lookup time again.
    if (constant, controller) in __settings_cache:
        return __settings_cache[(constant, controller)]
    if controller not in settings:
        raise Exception('Unable to find a setting for {}'.format(controller))

    setting_map = settings[controller]
    value, requested_type = setting_map[constant]

    while value in setting_map:
        value, _ = setting_map[value]

    # Are there multiple options of what the value can be?
    if isinstance(requested_type, tuple):
        # If the value is None and we allow None as an option, that is okay
        if value is None and type(None) in requested_type:
            pass
        # If the value is None and we don't allow that as an option, raise an exception
        elif value is None and type(None) not in requested_type:
            raise Exception('constant "{}" contains value: None, which is of type NoneType. Expected type: {}'.format(
                constant, requested_type
            ))
        # If value is not None and float is an option, use that. Float will take priority over int as well then
        elif value and float in requested_type:
            value = float(value)
    elif value and requested_type is float:
        value = float(value)

    # Set cache if we made it this far
    __settings_cache[(constant, controller)] = value
    return value


def get_window_constant(constant: str) -> Any:
    return _get_constant(constant, 'window')


def get_boxcar_constant(constant: str) -> Any:
    return _get_constant(constant, 'boxcar')


def get_ga_constant(constant: str) -> Any:
    return _get_constant(constant, 'ga')


def get_settings() -> Any:
    return settings


def update_settings_value(controller: str, constant: str, new_value: tuple, frame: int = -1, dir: str = "", file_name: str = "", should_log: bool = False):
    if should_log:
        if file_name not in os.listdir(dir):
            with open(os.path.join(dir, file_name), "w") as f:
                f.write("frame,controller,constant,old_value,new_value\n")

        with open(os.path.join(dir, file_name), "a") as f:
            f.write(f"{frame},{controller},{constant},{settings[controller][constant]},{new_value}\n")

    settings[controller][constant] = new_value
    __settings_cache[(constant, controller)] = new_value[0]
