time_rewards_x = [(10 * 60), (7.5 * 60), (5 * 60), (4 * 60), (3 * 60), (2 * 60), (1 * 60), (.75 * 60), (.5 * 60), (.25 * 60), (.1 * 60), (.05 * 60)]
time_rewards_y = [80,75,60,50,45,40,35,30,25,20,15, 0]

print(len(time_rewards_x), len(time_rewards_y))

import numpy as np
import math
from scipy.optimize import curve_fit

x = np.array(time_rewards_x)
y = np.array(time_rewards_y)

def fit_cubic_func(x, a, b, c, d):
    return (a * np.power(x, 3)) + (b * np.power(x, 2)) + (c * np.power(x, 1)) + d

def fit_square_func(x, a, b):
    return (a * np.power(x, 1/2)) + b

def fit_sinusoidal(x, a, b, c, d):
    return (a * np.sinc(b * np.pi * x)) + (c * np.pi * x) + d

def time_reward_function(time_difference):
    return (4806.8650485745911 * np.sinc(4.4358303100191581 * np.pi * x)) + (0.032158790024453009 * np.pi * x) + 25.347387598313965

chosen_func = fit_sinusoidal
params = curve_fit(chosen_func, x, y)
[a, b, c, d] = params[0]

print(a, b, c, d)

def correct_function(x):
    return chosen_func(x, a, b, c, d)

for x in xrange(0, 10*60):
    print(x, round(correct_function(x), 0))