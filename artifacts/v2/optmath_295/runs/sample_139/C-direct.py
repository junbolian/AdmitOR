import gurobipy as gp
from gurobipy import GRB

def solve(params):
    nodes = [0, 1, 2, 3, 4]
    arcs = [
        (0,1),(0,2),(0,3),(0,4),
        (1,0),(1,2),(1,3),(1,4),
        (2,0),(2,1),(2,3),(2,4),
        (3,0),(3,1),(3,2),(3,4),
        (4,0),(4,1),(4,2),(4,3),
    ]

    # Net balance per node: positive = supply (inflow), negative = demand (outflow)
    # Hub 0: net outflow 147 => balance = -147
    # Hub 1: net outflow 103 => balance = -103
    # Hub 2: balanced => 0
    # Hub 3: net inflow 205 => balance = +205
    # Hub 4: net inflow 45  => balance = +45
    balance = {
        0: -params["net_outflow_demand_hub0"],
        1: -params["net_outflow_demand_hub1"],
        2: 0.0,
        3:  params["net_inflow_supply_hub3"],
        4:  params["net_inflow_supply_hub4"],
    }

    fixed_cost = {
        (i,j): params[f"fixed_cost_{i}_{j}"] for (i,j) in arcs
    }
    capacity = {
        (i,j): params[f"capacity_{i}_{j}"] for (i,j) in arcs
    }
    variable_cost = {
        (i,j): params[f"variable_cost_{i}_{j}"] for (i,j) in arcs
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: establish connection
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    # Continuous: flow on each arc
    x = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: fixed costs + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[a] * y[a] + variable_cost[a] * x[a] for a in arcs),
        GRB.MINIMIZE
    )

    # Capacity constraints: flow <= capacity * establish
    for a in arcs:
        model.addConstr(x[a] <= capacity[a] * y[a], name=f"cap_{a[0]}_{a[1]}")

    # Flow balance: outflow - inflow = -balance (demand positive, supply negative)
    for n in nodes:
        outflow = gp.quicksum(x[a] for a in arcs if a[0] == n)
        inflow  = gp.quicksum(x[a] for a in arcs if a[1] == n)
        model.addConstr(outflow - inflow == -balance[n], name=f"balance_{n}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}