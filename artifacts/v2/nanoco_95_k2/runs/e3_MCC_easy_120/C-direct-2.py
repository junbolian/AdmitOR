import gurobipy as gp
from gurobipy import GRB

def solve(params):
    lower_bounds = params["lower_bounds"]
    upper_bounds = params["upper_bounds"]
    energy_costs = params["energy_costs"]
    num_units = params["num_units"]
    num_pipelines = params["num_pipelines"]

    # Pipeline connections (from_unit, to_unit) — structural definition
    pipelines = [
        (0, 1), (0, 3), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 6),
        (2, 1), (2, 3),
        (3, 2), (3, 4),
        (4, 2), (4, 3), (4, 5),
        (5, 4), (5, 6),
        (6, 0), (6, 5),
    ]

    model = gp.Model("biogas_recirculation")
    model.Params.OutputFlag = 0

    # Decision variables: flow rate on each pipeline
    f = {}
    for p in range(num_pipelines):
        f[p] = model.addVar(
            lb=lower_bounds[p],
            ub=upper_bounds[p],
            vtype=GRB.CONTINUOUS,
            name=f"flow_{p}",
        )

    model.update()

    # Flow conservation: total inflow == total outflow at each unit
    for u in range(num_units):
        inflow = gp.quicksum(f[p] for p in range(num_pipelines) if pipelines[p][1] == u)
        outflow = gp.quicksum(f[p] for p in range(num_pipelines) if pipelines[p][0] == u)
        model.addConstr(inflow == outflow, name=f"balance_{u}")

    # Objective: minimize total pumping energy consumption
    model.setObjective(
        gp.quicksum(f[p] * energy_costs[p] for p in range(num_pipelines)),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}