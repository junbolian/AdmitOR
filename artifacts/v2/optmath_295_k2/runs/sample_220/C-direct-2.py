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

    # Hubs: 0,1 are demand nodes; 2,3,4 are supply nodes
    # Net balance: positive = net demand (needs inflow), negative = net supply (produces outflow)
    # We define net_demand[i]: positive means hub i needs net inflow
    net_demand = {
        0:  demand_0,
        1:  demand_1,
        2: -supply_2,
        3: -supply_3,
        4: -supply_4,
    }

    hubs = [0, 1, 2, 3, 4]

    # Define all directed connections (arcs) between hubs
    # Supply hubs (2,3,4) ship to demand hubs (0,1), but we allow all pairs
    arcs = [(i, j) for i in hubs for j in hubs if i != j]

    # Assign fixed costs, variable costs, and capacities to each arc
    # Distribute evenly across arcs using a deterministic mapping
    n_arcs = len(arcs)  # 20 arcs

    # We interpolate fixed_cost, variable_cost, capacity across arcs
    # arc index k -> value = min + (max - min) * k / (n_arcs - 1)
    fixed_cost = {}
    variable_cost = {}
    capacity = {}
    for k, arc in enumerate(arcs):
        t = k / (n_arcs - 1) if n_arcs > 1 else 0.0
        fixed_cost[arc] = fixed_cost_min + (fixed_cost_max - fixed_cost_min) * t
        variable_cost[arc] = variable_cost_min + (variable_cost_max - variable_cost_min) * t
        capacity[arc] = capacity_min + (capacity_max - capacity_min) * t

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    # Binary: establish connection arc (i,j)
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")

    # Continuous: flow along arc (i,j)
    x = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[arc] * y[arc] + variable_cost[arc] * x[arc] for arc in arcs),
        GRB.MINIMIZE
    )

    # Capacity constraints: flow <= capacity * binary
    for arc in arcs:
        model.addConstr(x[arc] <= capacity[arc] * y[arc], name=f"cap_{arc[0]}_{arc[1]}")

    # Flow balance: inflow - outflow = net_demand[i]
    for i in hubs:
        inflow = gp.quicksum(x[(j, i)] for j in hubs if j != i)
        outflow = gp.quicksum(x[(i, j)] for j in hubs if j != i)
        model.addConstr(inflow - outflow == net_demand[i], name=f"balance_{i}")

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