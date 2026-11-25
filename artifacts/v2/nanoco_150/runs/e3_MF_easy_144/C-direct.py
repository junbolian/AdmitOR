import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    unit_costs = params["unit_costs"]
    # node_coordinates are frozen/structural; not used in objective or constraints

    edges = [
        (0,1),(1,2),(1,4),(1,5),(1,7),(2,3),(3,4),(4,5),(4,8),(4,9),
        (5,6),(5,7),(6,7),(7,8),(8,9)
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables for each directed edge
    flow = {}
    for idx, (u, v) in enumerate(edges):
        flow[(u, v)] = model.addVar(lb=0.0, ub=capacities[idx], name=f"f_{u}_{v}")

    # Maximize flow into sink node 9
    # Flow into node 9 comes from edges ending at 9
    sink_inflow = gp.quicksum(flow[(u, v)] for (u, v) in edges if v == 9)
    model.setObjective(sink_inflow, GRB.MAXIMIZE)

    # Flow conservation for intermediate nodes 1 through 8
    for node in range(1, 9):
        inflow = gp.quicksum(flow[(u, v)] for (u, v) in edges if v == node)
        outflow = gp.quicksum(flow[(u, v)] for (u, v) in edges if u == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}