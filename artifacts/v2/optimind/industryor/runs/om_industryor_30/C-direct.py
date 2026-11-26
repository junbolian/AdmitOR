import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]   # list of 4 values: [cap_A, cap_B, cap_C, cap_D]
    rate_A = params["rate_A"]       # list of 3 values: rates for components 1,2,3 at workshop A
    rate_B = params["rate_B"]
    rate_C = params["rate_C"]
    rate_D = params["rate_D"]

    workshops = range(4)   # 0=A, 1=B, 2=C, 3=D
    components = range(3)  # 0=1, 1=2, 2=3

    rates = [rate_A, rate_B, rate_C, rate_D]

    model = gp.Model("max_products")
    model.setParam("OutputFlag", 0)

    # x[w][c] = hours workshop w allocates to component c
    x = [[model.addVar(lb=0.0, name=f"x_{w}_{c}") for c in components] for w in workshops]

    # z = number of completed products
    z = model.addVar(lb=0.0, name="z")

    # Capacity constraints: sum over components of hours at each workshop <= capacity
    for w in workshops:
        model.addConstr(gp.quicksum(x[w][c] for c in components) <= capacity[w],
                        name=f"cap_{w}")

    # Completed products are limited by the total units produced of each component
    # Total units of component c = sum over workshops of rate[w][c] * x[w][c]
    # z <= total units of component c  for each c
    for c in components:
        model.addConstr(z <= gp.quicksum(rates[w][c] * x[w][c] for w in workshops),
                        name=f"comp_{c}")

    model.setObjective(z, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}