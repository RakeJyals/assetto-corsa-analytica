from math import floor, ceil
from statistics import mean
from scipy.optimize import brentq
import numpy as np


class Race:  # While technically redundant, this reduces repetition of typing out these parameters
    def __init__(self, length, long_stop_time, long_stop_count):
        self.length = length
        self.long_stop_time = long_stop_time
        self.long_stop_count = long_stop_count



class Driver:  # Updating driver values updates them in cars
    def __init__(self, name, laptime, fuel_consumption):
        self.name = name
        self.average_lap_time = laptime
        self.average_fuel_consumption = fuel_consumption



class Car:  # TODO driver data (should this be a method?), pitstop time
    def __init__(self, race, base_pitstop_loss, fuel_tank_size, refuel_rate, tire_swap_time):
        self.fuel_tank_size = fuel_tank_size
        self.refuel_rate = refuel_rate
        self.tire_swap_time = tire_swap_time
        self.base_pitstop_loss = base_pitstop_loss

        self.race_length = race.length
        self.long_stop_time = race.long_stop_time
        self.long_stop_count = race.long_stop_count

        self.drivers = []
        self.stint_lengths = []

        self.num_pitstops = None


    def add_driver(self, driver):
        self.drivers.append(driver)

        return


    def estimate_stint_length(self, driver = None, laps_per_stint = None):  # TODO refactor for sequence of drivers
        '''
        Method for determining the number of stints required to finish the race, along with how long the stints will last and the margin to running out of fuel.
        The estimated number of stints is a float number, eg. 1.2 stints means the driver should be 20% done with stint number 2 when the race ends.
        These estimates assume that the driver completes the same specified number of laps each stint.
        Max stint length is in seconds and includes time spent on pitstop.

        Inputs: 
        driver (defaults to first driver in the driver list if not specified)
        laps_per_stint (defaults to the maximum number of laps doable on one tank of fuel)
        '''  # TODO explain seconds_margin
        if not driver:
            driver = self.drivers[0]
        
        total_long_stop_time = self.long_stop_count * self.long_stop_time
        effective_race_length = self.race_length - total_long_stop_time

        if laps_per_stint:
            liters_to_refuel = laps_per_stint * driver.average_fuel_consumption
        else:
            liters_to_refuel = self.fuel_tank_size - driver.average_fuel_consumption  # To get a lower bound on max_stint_length, we lower bound pitstop length by
            # assuming there is at least one lap of fuel left in the tank when coming in

        pitstop_length = self.base_pitstop_loss + max(self.tire_swap_time, self.refuel_rate * liters_to_refuel)

        if not laps_per_stint:
            laps_per_stint = floor(self.fuel_tank_size / driver.average_fuel_consumption)  # TODO Can this be moved up to avoid having the previous if laps_per_stint block?
    
        max_stint_length = driver.average_lap_time * laps_per_stint + pitstop_length
        # TODO: Parameter for max laps out? (tire strategy, may be better to save for new strat calculator)

        stint_total = (effective_race_length + driver.average_lap_time) / max_stint_length  # Adding average_lap_time to numerator accounts for 6 hours + 1 lap
        # We want an upper bound of this
        # PROBLEM! Does not account for the fact that long stops have free pit stop!!!  Long stops are removed from numerator but also need to be removed from denominator
        # To fix, max_stint_length should be a weighted average of max_stint_length
        average_stint_length = driver.average_lap_time * laps_per_stint + ((stint_total - self.long_stop_count) / stint_total) * pitstop_length
        new_stint_total = (effective_race_length + driver.average_lap_time) / average_stint_length  # TODO make this a loop that breaks once it converges well enough

        # pitstop_length is the sum of the time lost between the inlap and outlap. The first stint does not have an outlap but rather a formation lap (which is longer than an outlap),
        # the final stint has an outlap but not an inlap. Therefore right now stint_total is overestimated by outlap_differential / max_stint_length

        seconds_margin = (round(new_stint_total) - new_stint_total) * average_stint_length
    
        return new_stint_total, max_stint_length, seconds_margin  # Separate function for max_stint_length?


    def laps_and_fuel_per_stint(self, driver = None):  # TODO refactor for sequence of drivers, different refuelings between short/long stops
        if not driver:
            driver = self.drivers[0]
        
        stint_total = self.num_pitstops + 1
        obj = lambda laps_per_stint: self.estimate_stint_length(driver.average_lap_time, 
                                                                driver.average_fuel_consumption, 
                                                                laps_per_stint)[0] - stint_total
        # Objective currently tries to calculate minimum fuel needed per stint to complete all stints

        # Calculate optimal laps per stint
        optimal_laps_per_stint = brentq(obj, 1, floor(self.fuel_tank_size / driver.average_fuel_consumption))

        # Return liters required to do optimal laps
        return floor(optimal_laps_per_stint), ceil(driver.average_fuel_consumption * optimal_laps_per_stint)


    def pit_time_matrix(self):  # TODO refactor for series of drivers
    # TODO: optional argument for start time, pit window opens/closes versions

        laps_per_stint, liters_to_refuel = self.laps_and_fuel_per_stint()
        _, stint_length, _ = self.estimate_stint_length(laps_per_stint = laps_per_stint)
        pitstop_length = self.base_pitstop_loss + max(self.tire_swap_time, self.refuel_rate * liters_to_refuel)

        # Create 1D arrays
        long_stop_array = np.arange(self.long_stops + 1).reshape((1, -1))
        pit_stops_array_base = np.arange(1, self.num_pitstops + 1).reshape((-1, 1))  # First element is before first pitstop (after first stint), last element is final pitstop

        # Convert pit_stops_array to times that car should enter pits if there are no long stops
        pit_stops_array = self.race_length - (pit_stops_array_base * stint_length) + pitstop_length  # Adding back pitstop_length is necessary since the pitstop hasn't been done on entry
        pit_stops_array = pit_stops_array.astype(np.int32)

        # Factor in long stops
        pit_stops_matrix = (pit_stops_array - self.long_stop_time * long_stop_array)

        # Convert array to timedelta
        pit_stops_matrix_seconds = (pit_stops_matrix % 60).astype(np.str_)
        pit_stops_matrix_minutes = ((pit_stops_matrix // 60) % 60).astype(np.str_)
        pit_stops_matrix_hours = (pit_stops_matrix // 3600).astype(np.str_)
        pit_stops_matrix_string = pit_stops_matrix_hours + ":" + pit_stops_matrix_minutes + ":" + pit_stops_matrix_seconds  # Consider printing strings line by line

        # Replace invalid elements of array with NaN (fewer long stops than stops completed and more long stops than pit stops remaining)
        pit_stops_matrix_string[(pit_stops_array_base <= long_stop_array) | (pit_stops_array_base - 1 > (len(long_stop_array) + long_stop_array))] = "NaN"

        return pit_stops_matrix_string


class GT3(Car):
    def __init__(self, race, base_pitstop_loss):
        super().__init__(race, base_pitstop_loss, fuel_tank_size=100, refuel_rate=0.353, tire_swap_time=30)


class LMP2(Car):
    def __init__(self, race, base_pitstop_loss):
        super().__init__(race, base_pitstop_loss, fuel_tank_size = 75, refuel_rate = 0.6, tire_swap_time = 10)