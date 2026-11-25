import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    node_supplies = params["node_supplies"]
    node_coordinates = params["node_coordinates"]

    arcs = [
        (0,1),(0,7),(1,2),(1,7),(2,3),(2,6),(3,4),(3,5),(3,8),(3,9),
        (4,5),(4,8),(5,6),(6,7),(7,8),(7,9),(8,9)
    ]
    num_arcs = 17
    num_nodes = 10

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    flow = model.addVars(num_arcs, lb=0.0, name="flow")

    for a in range(num_arcs):
        flow[a].ub = arc_capacities[a]

    model.setObjective(
        gp.quicksum(arc_costs[a] * flow[a] for a in range(num_arcs)),
        GRB.MINIMIZE
    )

    for n in range(num_nodes):
        outflow = gp.quicksum(flow[a] for a, (i, j) in enumerate(arcs) if i == n)
        inflow  = gp.quicksum(flow[a] for a, (i, j) in enumerate(arcs) if j == n)
        model.addConstr(outflow - inflow == node_supplies[n], name=f"balance_{n}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}