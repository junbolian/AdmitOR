import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["num_nodes"])
    nodes = range(n)

    # Build cost/capacity dicts from params
    fixed_cost = {}
    variable_cost = {}
    capacity = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                fixed_cost[(i, j)] = params[f"fixed_cost_{i}_{j}"]
                variable_cost[(i, j)] = params[f"variable_cost_{i}_{j}"]
                capacity[(i, j)] = params[f"capacity_{i}_{j}"]

    net_outflow = {
        0: params["net_outflow_node0"],
        1: params["net_outflow_node1"],
        2: params["net_outflow_node2"],
        3: params["net_outflow_node3"],
    }

    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    x = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[a] * y[a] + variable_cost[a] * x[a] for a in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints
    for i in nodes:
        model.addConstr(
            gp.quicksum(x[(i, j)] for j in nodes if j != i) -
            gp.quicksum(x[(j, i)] for j in nodes if j != i)
            == net_outflow[i],
            name=f"balance_{i}"
        )

    # Capacity and linking constraints
    for a in arcs:
        model.addConstr(x[a] <= capacity[a] * y[a], name=f"cap_{a[0]}_{a[1]}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}