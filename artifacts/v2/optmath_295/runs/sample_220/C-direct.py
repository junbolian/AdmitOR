import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_hub0 = params["demand_hub0"]
    demand_hub1 = params["demand_hub1"]
    supply_hub2 = params["supply_hub2"]
    supply_hub3 = params["supply_hub3"]
    supply_hub4 = params["supply_hub4"]
    fixed_cost_range = params["fixed_cost_range"]
    variable_cost_range = params["variable_cost_range"]
    capacity_range = params["capacity_range"]

    # Five hubs: 0,1 are demand hubs; 2,3,4 are supply hubs
    # Net balance: positive = net inflow required (demand), negative = net outflow available (supply)
    net_demand = {
        0:  demand_hub0,
        1:  demand_hub1,
        2: -supply_hub2,
        3: -supply_hub3,
        4: -supply_hub4,
    }

    hubs = list(range(5))

    # All directed arcs between distinct hubs
    arcs = [(i, j) for i in hubs for j in hubs if i != j]

    # Distribute fixed costs, variable costs, and capacities across arcs
    # using a simple linear interpolation so that the first arc gets the min
    # value and the last gets the max value.
    n_arcs = len(arcs)

    fc_min, fc_max = fixed_cost_range[0], fixed_cost_range[1]
    vc_min, vc_max = variable_cost_range[0], variable_cost_range[1]
    cap_min, cap_max = capacity_range[0], capacity_range[1]

    fixed_cost = {}
    variable_cost = {}
    capacity = {}

    for idx, arc in enumerate(arcs):
        t = idx / (n_arcs - 1) if n_arcs > 1 else 0.0
        fixed_cost[arc]    = fc_min  + t * (fc_max  - fc_min)
        variable_cost[arc] = vc_min  + t * (vc_max  - vc_min)
        capacity[arc]      = cap_min + t * (cap_max  - cap_min)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: whether arc (i,j) is established
    establish = model.addVars(arcs, vtype=GRB.BINARY, name="establish")

    # Continuous: flow on arc (i,j)
    flow = model.addVars(arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="flow")

    # Objective: minimize total fixed + variable cost
    model.setObjective(
        gp.quicksum(fixed_cost[a] * establish[a] + variable_cost[a] * flow[a] for a in arcs),
        GRB.MINIMIZE
    )

    # Capacity constraints: flow <= capacity * establish
    for a in arcs:
        model.addConstr(flow[a] <= capacity[a] * establish[a], name=f"cap_{a[0]}_{a[1]}")

    # Flow balance: inflow - outflow == net_demand[i]
    for i in hubs:
        inflow  = gp.quicksum(flow[(j, i)] for j in hubs if j != i)
        outflow = gp.quicksum(flow[(i, j)] for j in hubs if j != i)
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
        return {"objective": None, "status": f"solver_status_{status}"}