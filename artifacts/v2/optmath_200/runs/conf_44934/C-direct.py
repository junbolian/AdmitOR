import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    operational_cost_per_freq = params["operational_cost_per_freq"]
    capacity_per_trip = params["capacity_per_trip"]
    resource_usage_per_trip = params["resource_usage_per_trip"]
    min_frequency = params["min_frequency"]
    max_frequency = params["max_frequency"]
    demand = params["demand"]
    penalty_unmet = params["penalty_unmet"]
    total_resource_budget = params["total_resource_budget"]

    num_lines = 10
    od_keys = ["OD_6_7", "OD_6_1", "OD_3_0", "OD_4_6", "OD_1_0", "OD_5_3",
               "OD_4_2", "OD_4_1", "OD_1_4", "OD_2_3", "OD_4_0", "OD_6_4"]
    num_od = len(od_keys)

    # Lines indexed 0..9, OD pairs indexed 0..11
    lines = range(num_lines)
    ods = range(num_od)

    # Parse demand and penalty as lists
    if isinstance(demand, dict):
        demand_list = [demand[k] for k in od_keys]
    else:
        demand_list = list(demand)

    if isinstance(penalty_unmet, dict):
        penalty_list = [penalty_unmet[k] for k in od_keys]
    else:
        penalty_list = list(penalty_unmet)

    # Parse per-line params
    if isinstance(fixed_cost, dict):
        fc = [fixed_cost[f"L_{i}"] for i in lines]
    else:
        fc = list(fixed_cost)

    if isinstance(operational_cost_per_freq, dict):
        oc = [operational_cost_per_freq[f"L_{i}"] for i in lines]
    else:
        oc = list(operational_cost_per_freq)

    if isinstance(capacity_per_trip, dict):
        cap = [capacity_per_trip[f"L_{i}"] for i in lines]
    else:
        cap = list(capacity_per_trip)

    if isinstance(resource_usage_per_trip, dict):
        res = [resource_usage_per_trip[f"L_{i}"] for i in lines]
    else:
        res = list(resource_usage_per_trip)

    if isinstance(min_frequency, dict):
        min_freq = [min_frequency[f"L_{i}"] for i in lines]
    else:
        min_freq_val = min_frequency if not hasattr(min_frequency, '__iter__') else None
        if min_freq_val is not None:
            min_freq = [min_freq_val] * num_lines
        else:
            min_freq = list(min_frequency)

    if isinstance(max_frequency, dict):
        max_freq = [max_frequency[f"L_{i}"] for i in lines]
    else:
        max_freq_val = max_frequency if not hasattr(max_frequency, '__iter__') else None
        if max_freq_val is not None:
            max_freq = [max_freq_val] * num_lines
        else:
            max_freq = list(max_frequency)

    # Handle scalar min/max frequency
    try:
        _ = iter(min_freq)
    except TypeError:
        min_freq = [min_freq] * num_lines

    try:
        _ = iter(max_freq)
    except TypeError:
        max_freq = [max_freq] * num_lines

    # Since the problem doesn't define explicit line-to-OD coverage mapping,
    # we model each OD pair as potentially served by all lines (fully connected assumption).
    # Total capacity for OD pair p = sum over lines of cap[i] * freq[i] * coverage[i,p]
    # To keep the model tractable without explicit route data, we assume all lines
    # collectively contribute capacity and each line serves each OD pair.
    # The demand constraint: sum_i(cap[i] * freq[i]) + unmet[p] >= demand[p] for each p
    # This is a relaxation; with explicit coverage it would be tighter.
    # We use a binary coverage variable x[i] (line selected) and continuous freq[i].

    model = gp.Model("transit_network")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x[i]: 1 if line i is selected
    x = model.addVars(num_lines, vtype=GRB.BINARY, name="x")
    # f[i]: frequency of line i (continuous)
    f = model.addVars(num_lines, lb=0.0, name="f")
    # u[p]: unmet demand for OD pair p
    u = model.addVars(num_od, lb=0.0, name="u")

    # Frequency bounds linked to selection
    for i in lines:
        # f[i] >= min_freq[i] * x[i]
        model.addConstr(f[i] >= min_freq[i] * x[i], name=f"min_freq_{i}")
        # f[i] <= max_freq[i] * x[i]
        model.addConstr(f[i] <= max_freq[i] * x[i], name=f"max_freq_{i}")

    # Resource constraint
    model.addConstr(
        gp.quicksum(res[i] * f[i] for i in lines) <= total_resource_budget,
        name="resource_budget"
    )

    # Demand satisfaction: total capacity across all lines + unmet >= demand
    # Since no explicit route-OD coverage is given, all lines serve all OD pairs
    total_capacity = gp.quicksum(cap[i] * f[i] for i in lines)
    for p in ods:
        model.addConstr(
            total_capacity + u[p] >= demand_list[p],
            name=f"demand_{p}"
        )

    # Unmet demand cannot exceed total demand
    for p in ods:
        model.addConstr(u[p] <= demand_list[p], name=f"unmet_cap_{p}")

    # Objective: minimize fixed costs + operational costs + penalty for unmet demand
    obj = (
        gp.quicksum(fc[i] * x[i] for i in lines) +
        gp.quicksum(oc[i] * f[i] for i in lines) +
        gp.quicksum(penalty_list[p] * u[p] for p in ods)
    )
    model.setObjective(obj, GRB.MINIMIZE)

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