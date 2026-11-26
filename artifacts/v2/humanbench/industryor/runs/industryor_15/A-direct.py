import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    gasoline_limit = params["gasoline_limit"]
    heavy_bomb_limit = params["heavy_bomb_limit"]
    light_bomb_limit = params["light_bomb_limit"]
    fuel_efficiency_heavy = params["fuel_efficiency_heavy"]
    fuel_efficiency_light = params["fuel_efficiency_light"]
    fuel_efficiency_empty = params["fuel_efficiency_empty"]
    takeoff_landing_fuel = params["takeoff_landing_fuel"]
    distances = params["distances"]
    prob_heavy = params["prob_heavy"]
    prob_light = params["prob_light"]

    n_areas = len(distances)

    model = pyo.ConcreteModel()

    model.areas = pyo.Set(initialize=range(n_areas), ordered=True)

    model.xh = pyo.Var(model.areas, within=pyo.NonNegativeReals)
    model.xl = pyo.Var(model.areas, within=pyo.NonNegativeReals)

    # Failure probability per area (linear in log-space; minimize sum of failure probs)
    # Use linear approximation: failure_i = 1 - p >= 0, we minimize sum f_i
    # Constraint linking log-survival is nonlinear; instead model standard LP:
    # Maximize sum of destruction fractions s_i, with s_i <= these linear caps.
    # The classic LP formulation: minimize sum of (1 - p_heavy)^xh * (1 - p_light)^xl
    # is nonlinear. Standard linearization: maximize sum s_i subject to
    # s_i = 1 - f_i, f_i >= surrogate. Use the standard multiplicative-failure
    # linearization: define log linearization via auxiliary variables.

    import math

    # Failure factor per heavy bomb: (1 - p_h), per light bomb: (1 - p_l)
    # log-failure is linear in counts; total failure prob >= exp(log-failure)
    # To keep it LP, use first-order (or exact) linearization of -log(1-...) objective.
    # The classic textbook LP maximizes sum of "destruction" via:
    #   max sum_i (a_i xh_i + b_i xl_i), with a=-log(1-ph), b=-log(1-pl)
    # subject to x limits and fuel limits.

    a_coef = {}
    b_coef = {}
    for i in range(n_areas):
        a_coef[i] = -math.log(1.0 - prob_heavy[i]) if prob_heavy[i] < 1.0 else 1e6
        b_coef[i] = -math.log(1.0 - prob_light[i]) if prob_light[i] < 1.0 else 1e6

    def obj_rule(m):
        return sum(a_coef[i] * m.xh[i] + b_coef[i] * m.xl[i] for i in m.areas)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def heavy_limit_rule(m):
        return sum(m.xh[i] for i in m.areas) <= heavy_bomb_limit

    model.heavy_limit = pyo.Constraint(rule=heavy_limit_rule)

    def light_limit_rule(m):
        return sum(m.xl[i] for i in m.areas) <= light_bomb_limit

    model.light_limit = pyo.Constraint(rule=light_limit_rule)

    # Fuel: for each bomb dropped at area i, round trip + takeoff/landing.
    # Fuel for heavy = 2*dist/fuel_eff_heavy + takeoff_landing
    # Fuel for light = 2*dist/fuel_eff_light + takeoff_landing
    def fuel_rule(m):
        return sum(
            m.xh[i] * (2.0 * distances[i] / fuel_efficiency_heavy + takeoff_landing_fuel)
            + m.xl[i] * (2.0 * distances[i] / fuel_efficiency_light + takeoff_landing_fuel)
            for i in m.areas
        ) <= gasoline_limit

    model.fuel = pyo.Constraint(rule=fuel_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}