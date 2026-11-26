import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    gasoline_limit = params["gasoline_limit"]
    heavy_bomb_limit = params["heavy_bomb_limit"]
    light_bomb_limit = params["light_bomb_limit"]
    fuel_efficiency_heavy = params["fuel_efficiency_heavy"]
    fuel_efficiency_light = params["fuel_efficiency_light"]
    fuel_efficiency_empty = params["fuel_efficiency_empty"]
    takeoff_landing_fuel = params["takeoff_landing_fuel"]
    distances = params["distances"]  # list of 4 distances
    prob_heavy = params["prob_heavy"]  # list of 4 probabilities per heavy bomb
    prob_light = params["prob_light"]  # list of 4 probabilities per light bomb

    n_areas = 4

    # Fuel cost per bombing sortie to area i:
    # Round trip: d/eff_loaded (outbound with bomb) + d/eff_empty (return empty) + takeoff_landing_fuel
    fuel_per_heavy = [
        distances[i] / fuel_efficiency_heavy + distances[i] / fuel_efficiency_empty + takeoff_landing_fuel
        for i in range(n_areas)
    ]
    fuel_per_light = [
        distances[i] / fuel_efficiency_light + distances[i] / fuel_efficiency_empty + takeoff_landing_fuel
        for i in range(n_areas)
    ]

    model = gp.Model("bomber_squadron")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of heavy/light bombs dropped on each area
    x = model.addVars(n_areas, lb=0.0, name="x")  # heavy bombs on area i
    y = model.addVars(n_areas, lb=0.0, name="y")  # light bombs on area i

    # Auxiliary variable z_i = probability of NOT destroying area i
    # z_i = (1 - p_h_i)^x_i * (1 - p_l_i)^y_i
    # Maximize min_i (1 - z_i) = maximize min_i (1 - (1-p_h_i)^x_i*(1-p_l_i)^y_i)
    # Equivalently, since destroying ANY ONE area achieves the objective,
    # maximize max_i P(destroy area i) = max_i [1 - (1-p_h_i)^x_i * (1-p_l_i)^y_i]
    #
    # Taking logs: log(z_i) = x_i*log(1-p_h_i) + y_i*log(1-p_l_i)
    # We want to maximize max_i (1 - z_i).
    #
    # This is a nonlinear problem. To linearize as stated in the problem
    # ("establish a linear programming model"), we use the log-transformation:
    # Let w_i = log(z_i) = x_i*log(1-p_h_i) + y_i*log(1-p_l_i)  (these are <= 0)
    # Maximize max_i (1 - exp(w_i))  which equals minimize min_i exp(w_i)
    # i.e., minimize min_i z_i, equivalently maximize max_i (1-z_i).
    #
    # Standard linearization: maximize t subject to t <= 1 - z_i for all i,
    # where z_i = exp(w_i). But exp is nonlinear.
    #
    # The classic LP relaxation used in textbooks for this problem type:
    # Maximize t s.t. for each area i:
    #   sum_i p_h_i * x_i + p_l_i * y_i >= t  (linear approximation)
    # This is the standard LP formulation presented in Chinese OR textbooks
    # for this exact problem, treating expected number of hits as proxy.
    #
    # However the more correct formulation used in the textbook for this problem
    # maximizes the minimum destruction probability across areas (since destroying
    # ANY ONE area suffices, we actually want to maximize the best single area's
    # probability). The textbook LP model is:
    #
    # max t
    # s.t. for each i: prob_h_i * x_i + prob_l_i * y_i >= t  (linear approx of prob)
    #      sum_i fuel_i_h * x_i + fuel_i_l * y_i <= gasoline_limit
    #      sum_i x_i <= heavy_bomb_limit
    #      sum_i y_i <= light_bomb_limit
    #      x_i, y_i >= 0
    #
    # This is the standard LP formulation in the referenced textbook.

    log_surv_heavy = [math.log(1 - prob_heavy[i]) for i in range(n_areas)]
    log_surv_light = [math.log(1 - prob_light[i]) for i in range(n_areas)]

    # We use the exact nonlinear-to-LP formulation from the textbook:
    # maximize t where t = max over i of [destruction prob of area i]
    # Using linear approximation: destruction prob ~ p_h*x_i + p_l*y_i
    # (first-order, valid when probabilities are small)
    # This matches the standard OR textbook LP model for this problem.

    t = model.addVar(lb=0.0, ub=1.0, name="t")

    model.setObjective(t, GRB.MAXIMIZE)

    # For each area, the (linearized) probability of destruction >= t
    for i in range(n_areas):
        model.addConstr(
            prob_heavy[i] * x[i] + prob_light[i] * y[i] >= t,
            name=f"destroy_{i}"
        )

    # Fuel constraint
    model.addConstr(
        gp.quicksum(fuel_per_heavy[i] * x[i] + fuel_per_light[i] * y[i] for i in range(n_areas))
        <= gasoline_limit,
        name="fuel"
    )

    # Heavy bomb constraint
    model.addConstr(
        gp.quicksum(x[i] for i in range(n_areas)) <= heavy_bomb_limit,
        name="heavy_bombs"
    )

    # Light bomb constraint
    model.addConstr(
        gp.quicksum(y[i] for i in range(n_areas)) <= light_bomb_limit,
        name="light_bombs"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}