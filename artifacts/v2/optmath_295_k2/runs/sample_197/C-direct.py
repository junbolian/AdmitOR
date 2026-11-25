import gurobipy as gp
from gurobipy import GRB

def solve(params):
    def get_param(prm, *keys):
        for k in keys:
            if k in prm:
                return prm[k]
        raise KeyError(f"None of {keys} found. Available keys: {list(prm.keys())}")

    cost = get_param(params,
        "cost", "costs", "cost_matrix", "c", "C",
        "travel_cost", "travel_costs", "travel_cost_matrix",
        "distance", "distances", "distance_matrix",
        "base", "cost_mat", "weight", "weights", "weight_matrix",
        "edge_cost", "edge_costs", "arc_cost", "arc_costs",
        "tsp_cost", "routing_cost", "Cost", "COST", "cost_data",
        "cost_table")

    position_city0 = get_param(params,
        "position_city0", "pos_city0", "p0", "position_0",
        "city0_position", "fixed_position", "pos0",
        "depot_position", "start_position", "city_0_position",
        "p_0", "u_0", "u0", "position0", "pos_0", "city0_pos")

    position_min_others = get_param(params,
        "position_min_others", "pos_min_others", "p_min", "pos_min",
        "min_position", "position_min", "lb_others", "min_pos_others",
        "lower_bound", "lb", "min_pos", "min_position_others",
        "p_min_others", "min_others")

    position_max_others = get_param(params,
        "position_max_others", "pos_max_others", "p_max", "pos_max",
        "max_position", "position_max", "ub_others", "max_pos_others",
        "upper_bound", "ub", "max_pos", "max_position_others",
        "p_max_others", "max_others")

    n = 4
    cities = list(range(n))
    non_depot = [i for i in cities if i != 0]

    model = gp.Model("tsp")
    model.Params.OutputFlag = 0

    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    p = {}
    for i in cities:
        p[i] = model.addVar(vtype=GRB.INTEGER, lb=0, ub=n, name=f"p_{i}")

    model.update()

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE,
    )

    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"out_{i}")

    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"in_{j}")

    model.addConstr(p[0] == position_city0, name="p0_fixed")

    for i in non_depot:
        model.addConstr(p[i] >= position_min_others, name=f"p_min_{i}")
        model.addConstr(p[i] <= position_max_others, name=f"p_max_{i}")

    M = n
    for i in non_depot:
        for j in non_depot:
            if i != j:
                model.addConstr(
                    p[j] >= p[i] + 1 - M * (1 - x[i, j]),
                    name=f"mtz_{i}_{j}",
                )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "infeasible"}