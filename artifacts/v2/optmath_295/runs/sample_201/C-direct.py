import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_aircraft = 6
    num_routes = 7

    availability = params["availability"]
    route_demand = params["route_demand"]
    route6_demand = params["route6_demand"]
    operational_cost = params["operational_cost"]

    # Build demand list; use route6_demand for route_6
    demand = list(route_demand)
    demand[6] = route6_demand

    # Build capacity matrix for all 6 aircraft types
    # a0_capacity and a1_capacity are explicitly listed in PARAMS;
    # a2_capacity through a5_capacity follow the same naming pattern.
    # Fallback: a "capacity" key holding a 6x7 matrix.
    capacity = []
    for i in range(num_aircraft):
        cap_key = f"a{i}_capacity"
        if cap_key in params:
            capacity.append(list(params[cap_key]))
        elif "capacity" in params:
            capacity = [list(params["capacity"][i]) for i in range(num_aircraft)]
            break
        else:
            raise KeyError(f"Cannot find capacity data for aircraft_{i}")

    model = gp.Model("airline_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = number of aircraft type i assigned to route j
    x = [[model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
          for j in range(num_routes)]
         for i in range(num_aircraft)]

    # Objective: minimize total operational cost
    model.setObjective(
        gp.quicksum(operational_cost[i][j] * x[i][j]
                    for i in range(num_aircraft)
                    for j in range(num_routes)),
        GRB.MINIMIZE
    )

    # Availability constraints: total aircraft of type i across all routes <= availability[i]
    for i in range(num_aircraft):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_routes)) <= availability[i],
            name=f"avail_{i}"
        )

    # Route demand constraints: combined capacity >= demand for each route
    for j in range(num_routes):
        model.addConstr(
            gp.quicksum(capacity[i][j] * x[i][j] for i in range(num_aircraft)) >= demand[j],
            name=f"demand_{j}"
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