import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_0 = params["supply_0"]
    supply_1 = params["supply_1"]
    supply_2 = params["supply_2"]
    supply_3 = params["supply_3"]
    demand_4 = params["demand_4"]
    demand_5 = params["demand_5"]
    capacity = params["capacity"]
    unit_cost = params["unit_cost"]

    # Node supplies (demand nodes have negative supply)
    node_supply = {
        0: supply_0,
        1: supply_1,
        2: supply_2,
        3: supply_3,
        4: -demand_4,
        5: -demand_5,
    }

    # Arc definitions in order: (0-2,0-3,1-2,1-3,2-4,2-5,3-4,3-5,0-4,0-5,1-4,1-5)
    arcs = [
        (0, 2), (0, 3), (1, 2), (1, 3),
        (2, 4), (2, 5), (3, 4), (3, 5),
        (0, 4), (0, 5), (1, 4), (1, 5),
    ]

    arc_capacity = {arcs[i]: capacity[i] for i in range(len(arcs))}
    arc_cost = {arcs[i]: unit_cost[i] for i in range(len(arcs))}

    model = gp.Model("medical_supply_chain")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow on each arc
    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for arc in arcs:
        model.addConstr(flow[arc] <= arc_capacity[arc], name=f"cap_{arc[0]}_{arc[1]}")

    # Flow balance constraints: outflow - inflow = supply at each node
    for node in range(6):
        outflow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == node)
        inflow = gp.quicksum(flow[arc] for arc in arcs if arc[1] == node)
        model.addConstr(outflow - inflow == node_supply[node], name=f"balance_{node}")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(arc_cost[arc] * flow[arc] for arc in arcs),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}