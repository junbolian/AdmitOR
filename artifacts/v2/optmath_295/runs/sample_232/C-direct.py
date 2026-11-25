import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]
    net_outflow = params["net_outflow"]

    nodes = [0, 1, 2, 3]
    # Directed routes ordered: 0->1,0->2,0->3,1->0,1->2,1->3,2->0,2->1,2->3,3->0,3->1,3->2
    arcs = [(0,1),(0,2),(0,3),(1,0),(1,2),(1,3),(2,0),(2,1),(2,3),(3,0),(3,1),(3,2)]

    arc_index = {arc: i for i, arc in enumerate(arcs)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: whether route is established
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    # Continuous: flow on each route
    x = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: fixed costs + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[arc_index[a]] * y[a] + variable_cost[arc_index[a]] * x[a] for a in arcs),
        GRB.MINIMIZE
    )

    # Capacity constraints: flow <= capacity * established
    for a in arcs:
        idx = arc_index[a]
        model.addConstr(x[a] <= capacity[idx] * y[a], name=f"cap_{a[0]}_{a[1]}")

    # Flow balance: outflow - inflow = net_outflow at each node
    for n in nodes:
        out_arcs = [a for a in arcs if a[0] == n]
        in_arcs  = [a for a in arcs if a[1] == n]
        model.addConstr(
            gp.quicksum(x[a] for a in out_arcs) - gp.quicksum(x[a] for a in in_arcs) == net_outflow[n],
            name=f"balance_{n}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}