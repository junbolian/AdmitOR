import gurobipy as gp
from gurobipy import GRB

def solve(params):
    T = 5
    types = [0, 1]

    base_cost = {0: params["base_cost_type0"], 1: params["base_cost_type1"]}
    power_cost = {0: params["power_cost_type0"], 1: params["power_cost_type1"]}
    startup_cost = {0: params["startup_cost_type0"], 1: params["startup_cost_type1"]}
    demand = params["demand"]
    min_output = {0: params["min_output_type0"], 1: params["min_output_type1"]}
    max_output = {0: params["max_output_type0"], 1: params["max_output_type1"]}
    reserve_margin = params["reserve_margin"]
    max_active = params["max_active_per_type"]
    max_startups_first = {0: params["max_startups_first_type0"], 1: params["max_startups_first_type1"]}

    model = gp.Model("unit_commitment")
    model.Params.OutputFlag = 0

    active = model.addVars(T, types, vtype=GRB.INTEGER, lb=0, ub=max_active, name="active")
    startup = model.addVars(T, types, vtype=GRB.INTEGER, lb=0, ub=max_active, name="startup")
    power = model.addVars(T, types, vtype=GRB.CONTINUOUS, lb=0, name="power")

    model.setObjective(
        gp.quicksum(
            base_cost[g] * active[t, g]
            + power_cost[g] * power[t, g]
            + startup_cost[g] * startup[t, g]
            for t in range(T) for g in types
        ),
        GRB.MINIMIZE
    )

    for t in range(T):
        model.addConstr(
            gp.quicksum(power[t, g] for g in types) >= demand[t],
            name=f"demand_{t}"
        )

    for t in range(T):
        for g in types:
            model.addConstr(
                power[t, g] >= min_output[g] * active[t, g],
                name=f"min_power_{t}_{g}"
            )
            model.addConstr(
                power[t, g] <= max_output[g] * active[t, g],
                name=f"max_power_{t}_{g}"
            )

    for t in range(T):
        model.addConstr(
            gp.quicksum(max_output[g] * active[t, g] for g in types)
            >= demand[t] * (1.0 + reserve_margin),
            name=f"reserve_{t}"
        )

    for g in types:
        model.addConstr(active[0, g] <= startup[0, g], name=f"active_init_{g}")
        model.addConstr(startup[0, g] <= max_startups_first[g], name=f"startup_init_{g}")
        for t in range(1, T):
            model.addConstr(
                active[t, g] <= active[t - 1, g] + startup[t, g],
                name=f"carry_{t}_{g}"
            )
            model.addConstr(
                startup[t, g] <= active[t, g] - active[t - 1, g],
                name=f"startup_limit_{t}_{g}"
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}