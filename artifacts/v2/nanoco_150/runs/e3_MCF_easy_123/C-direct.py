import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supplies = params["supplies"]
    capacities = params["capacities"]
    costs = params["costs"]

    arcs = [(0,2),(0,3),(1,2),(1,3),(2,4),(2,5),(3,4),(3,5),(0,4),(0,5),(1,4),(1,5)]
    nodes = list(range(6))

    model = gp.Model("ev_load_balancing")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    for i, arc in enumerate(arcs):
        flow[arc].ub = capacities[i]

    model.setObjective(
        gp.quicksum(costs[i] * flow[arcs[i]] for i in range(len(arcs))),
        GRB.MINIMIZE
    )

    for node in nodes:
        outflow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == node)
        inflow  = gp.quicksum(flow[arc] for arc in arcs if arc[1] == node)
        model.addConstr(outflow - inflow == supplies[node], name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}