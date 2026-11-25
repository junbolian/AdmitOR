import gurobipy as gp
from gurobipy import GRB


def solve(params):
    arcs_list = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4), (3, 7),
        (4, 5),
        (5, 6), (5, 7),
        (6, 7), (6, 8),
        (7, 8),
    ]

    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    source_supply = params["source_supply"]
    sink_supply = params["sink_supply"]
    intermediate_node_supply = params["intermediate_node_supply"]

    cost = {arcs_list[i]: arc_costs[i] for i in range(len(arcs_list))}
    cap = {arcs_list[i]: arc_capacities[i] for i in range(len(arcs_list))}

    nodes = list(range(9))
    supply = {}
    supply[0] = source_supply
    supply[8] = sink_supply
    if isinstance(intermediate_node_supply, (list, tuple)):
        for i, n in enumerate(range(1, 8)):
            supply[n] = intermediate_node_supply[i]
    else:
        for n in range(1, 8):
            supply[n] = intermediate_node_supply

    model = gp.Model("amr_path")
    model.Params.OutputFlag = 0

    x = {}
    for a in arcs_list:
        x[a] = model.addVar(lb=0, ub=cap[a], vtype=GRB.CONTINUOUS, name=f"x_{a[0]}_{a[1]}")

    model.setObjective(gp.quicksum(cost[a] * x[a] for a in arcs_list), GRB.MINIMIZE)

    for n in nodes:
        inflow = gp.quicksum(x[a] for a in arcs_list if a[1] == n)
        outflow = gp.quicksum(x[a] for a in arcs_list if a[0] == n)
        model.addConstr(outflow - inflow == supply[n], name=f"flow_balance_{n}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "infeasible"}