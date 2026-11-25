import gurobipy as gp
from gurobipy import GRB

def solve(params):
    unit_cost = params["unit_cost"]
    min_flow = params["min_flow"]
    capacity = params["capacity"]
    num_nodes = params["num_nodes"]
    num_pipes = params["num_pipes"]

    # Ordered list of directed pipes, matching the parameter ordering.
    edges = [
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 3),
        (3, 2), (3, 4),
        (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 3), (5, 4),
    ]
    assert len(edges) == num_pipes

    model = gp.Model("cooling_recirculation")
    model.Params.OutputFlag = 0

    # Flow variable per pipe, bounded by mandatory minimum and hydraulic capacity.
    flow = {}
    for i, (u, v) in enumerate(edges):
        flow[i] = model.addVar(
            lb=min_flow[i],
            ub=capacity[i],
            vtype=GRB.CONTINUOUS,
            name=f"flow_{u}_{v}",
        )

    # Perfect internal recirculation: inflow == outflow at every junction.
    for n in range(num_nodes):
        inflow = gp.quicksum(flow[i] for i, (u, v) in enumerate(edges) if v == n)
        outflow = gp.quicksum(flow[i] for i, (u, v) in enumerate(edges) if u == n)
        model.addConstr(inflow == outflow, name=f"balance_{n}")

    # Minimize total pumping energy consumption.
    model.setObjective(
        gp.quicksum(unit_cost[i] * flow[i] for i in range(num_pipes)),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}