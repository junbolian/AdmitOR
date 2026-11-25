import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_0 = params["demand_0"]
    demand_1 = params["demand_1"]
    supply_2 = params["supply_2"]
    supply_3 = params["supply_3"]
    supply_4 = params["supply_4"]
    fixed_cost_min = params["fixed_cost_min"]
    fixed_cost_max = params["fixed_cost_max"]
    variable_cost_min = params["variable_cost_min"]
    variable_cost_max = params["variable_cost_max"]
    capacity_min = params["capacity_min"]
    capacity_max = params["capacity_max"]

    # Hubs: 0,1 are demand hubs; 2,3,4 are supply hubs
    # Net balance: positive = net demand (sink), negative = net supply (source)
    # balance[i]: flow_in[i] - flow_out[i] = balance[i]
    # For demand hubs: balance = +demand
    # For supply hubs: balance = -supply
    balance = {
        0:  demand_0,
        1:  demand_1,
        2: -supply_2,
        3: -supply_3,
        4: -supply_4,
    }

    # Define all directed arcs (i -> j) for i != j, 5 hubs
    hubs = [0, 1, 2, 3, 4]
    arcs = [(i, j) for i in hubs for j in hubs if i != j]

    # Assign fixed costs, variable costs, capacities using min/max range
    # Distribute evenly across arcs using interpolation
    n_arcs = len(arcs)

    fixed_cost = {}
    variable_cost = {}
    capacity = {}

    for idx, (i, j) in enumerate(arcs):
        if n_arcs > 1:
            t = idx / (n_arcs - 1)
        else:
            t = 0.0
        fixed_cost[(i, j)] = fixed_cost_min + t * (fixed_cost_max - fixed_cost_min)
        variable_cost[(i, j)] = variable_cost_min + t * (variable_cost_max - variable_cost_min)
        capacity[(i, j)] = capacity_min + t * (capacity_max - capacity_min)

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    # Binary: whether arc (i,j) is established
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    # Continuous: flow on arc (i,j)
    x = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[a] * y[a] + variable_cost[a] * x[a] for a in arcs),
        GRB.MINIMIZE
    )

    # Capacity constraints: x[i,j] <= capacity[i,j] * y[i,j]
    for a in arcs:
        model.addConstr(x[a] <= capacity[a] * y[a], name=f"cap_{a[0]}_{a[1]}")

    # Flow balance: inflow - outflow = balance[i]
    for hub in hubs:
        inflow = gp.quicksum(x[(i, hub)] for i in hubs if i != hub)
        outflow = gp.quicksum(x[(hub, j)] for j in hubs if j != hub)
        model.addConstr(inflow - outflow == balance[hub], name=f"balance_{hub}")

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