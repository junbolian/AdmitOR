import gurobipy as gp
from gurobipy import GRB


def solve(params):
    lower_bounds = [float(v) for v in params["lower_bounds"]]
    upper_bounds = [float(v) for v in params["upper_bounds"]]
    energy_costs = [float(v) for v in params["energy_costs"]]
    unit_coords = params["unit_coords"]
    num_units = int(params["num_units"])
    num_pipelines = int(params["num_pipelines"])

    edges = [
        (0, 1), (0, 3), (0, 6), (1, 0), (1, 2), (1, 3),
        (1, 6), (2, 1), (2, 3), (3, 2), (3, 4), (4, 2),
        (4, 3), (4, 5), (5, 4), (5, 6), (6, 0), (6, 5),
    ]

    if num_pipelines != len(edges):
        return {"objective": None, "status": "pipeline_count_mismatch"}
    if num_units <= 0 or max(max(e) for e in edges) >= num_units:
        return {"objective": None, "status": "unit_count_mismatch"}
    if len(lower_bounds) != num_pipelines or len(upper_bounds) != num_pipelines or len(energy_costs) != num_pipelines:
        return {"objective": None, "status": "param_length_mismatch"}
    if len(unit_coords) != num_units:
        return {"objective": None, "status": "coord_length_mismatch"}
    for k in range(num_pipelines):
        if lower_bounds[k] > upper_bounds[k]:
            return {"objective": None, "status": "bound_conflict"}

    model = gp.Model("digestate_recirculation")
    model.setParam("OutputFlag", 0)

    flow = []
    for k in range(num_pipelines):
        flow.append(model.addVar(
            lb=lower_bounds[k],
            ub=upper_bounds[k],
            vtype=GRB.CONTINUOUS,
            name=f"flow_{k}",
        ))

    model.setObjective(
        gp.quicksum(energy_costs[k] * flow[k] for k in range(num_pipelines)),
        GRB.MINIMIZE,
    )

    for u in range(num_units):
        inflow = gp.quicksum(flow[k] for k in range(num_pipelines) if edges[k][1] == u)
        outflow = gp.quicksum(flow[k] for k in range(num_pipelines) if edges[k][0] == u)
        model.addConstr(inflow == outflow, name=f"balance_{u}")

    try:
        model.optimize()
    except gp.GurobiError:
        return {"objective": None, "status": "solver_error"}

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": f"status_{model.status}"}