import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost_facility"]      # list or dict: facility -> cost
    capacity   = params["capacity_facility"]         # list or dict: facility -> capacity
    demand     = params["demand_customer"]           # list or dict: customer -> demand
    ship_cost  = params["shipping_cost_per_unit"]    # list/dict/nested: (facility, customer) -> cost

    # Normalize fixed_cost to a dict keyed by facility name
    if isinstance(fixed_cost, dict):
        fixed_cost_dict = fixed_cost
    else:
        fixed_cost_dict = {f"facility_{i}": v for i, v in enumerate(fixed_cost)}

    # Normalize capacity to a dict keyed by facility name
    if isinstance(capacity, dict):
        capacity_dict = capacity
    else:
        capacity_dict = {f"facility_{i}": v for i, v in enumerate(capacity)}

    # Normalize demand to a dict keyed by customer name
    if isinstance(demand, dict):
        demand_dict = demand
    else:
        demand_dict = {f"customer_{i}": v for i, v in enumerate(demand)}

    facilities = list(fixed_cost_dict.keys())
    customers  = list(demand_dict.keys())

    # Normalize shipping cost to a dict keyed by (facility, customer)
    if isinstance(ship_cost, dict):
        # Could be {(f,c): cost} or {"facility_0": {"customer_0": cost, ...}, ...}
        first_key = next(iter(ship_cost))
        if isinstance(first_key, tuple):
            ship_cost_dict = ship_cost
        else:
            # nested dict: ship_cost[facility][customer] = cost
            ship_cost_dict = {}
            for f in facilities:
                for c in customers:
                    ship_cost_dict[(f, c)] = ship_cost[f][c]
    else:
        # list of lists: ship_cost[i][j]
        ship_cost_dict = {}
        for i, f in enumerate(facilities):
            for j, c in enumerate(customers):
                ship_cost_dict[(f, c)] = ship_cost[i][j]

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # Decision variables
    open_fac = model.addVars(facilities, vtype=GRB.BINARY, name="open")
    ship     = model.addVars(facilities, customers, lb=0.0, name="ship")

    # Objective: fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost_dict[f] * open_fac[f] for f in facilities) +
        gp.quicksum(ship_cost_dict[(f, c)] * ship[f, c] for f in facilities for c in customers),
        GRB.MINIMIZE
    )

    # Demand satisfaction
    for c in customers:
        model.addConstr(
            gp.quicksum(ship[f, c] for f in facilities) == demand_dict[c],
            name=f"demand_{c}"
        )

    # Capacity constraints
    for f in facilities:
        model.addConstr(
            gp.quicksum(ship[f, c] for c in customers) <= capacity_dict[f] * open_fac[f],
            name=f"capacity_{f}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}