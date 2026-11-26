import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_A = params["capacity_A"]
    capacity_B = params["capacity_B"]
    capacity_C = params["capacity_C"]
    capacity_D = params["capacity_D"]

    # productivity[workshop] = [units/hour for component 1, 2, 3]
    productivity_A = params["productivity_A"]  # list of 3 values
    productivity_B = params["productivity_B"]
    productivity_C = params["productivity_C"]
    productivity_D = params["productivity_D"]

    workshops = ["A", "B", "C", "D"]
    components = [0, 1, 2]  # indices for components 1, 2, 3

    capacities = {
        "A": capacity_A,
        "B": capacity_B,
        "C": capacity_C,
        "D": capacity_D,
    }

    productivity = {
        "A": productivity_A,
        "B": productivity_B,
        "C": productivity_C,
        "D": productivity_D,
    }

    model = gp.Model("completed_products")
    model.setParam("OutputFlag", 0)

    # x[w][c] = hours allocated to workshop w for component c
    x = {
        (w, c): model.addVar(lb=0.0, name=f"x_{w}_{c}")
        for w in workshops
        for c in components
    }

    # z = number of completed products (each product needs 1 of each component)
    z = model.addVar(lb=0.0, name="z")

    # Maximize completed products
    model.setObjective(z, GRB.MAXIMIZE)

    # Capacity constraints: total hours used at each workshop <= capacity
    for w in workshops:
        model.addConstr(
            gp.quicksum(x[w, c] for c in components) <= capacities[w],
            name=f"capacity_{w}"
        )

    # Component balance: total units of each component produced >= z
    # Units of component c = sum over workshops of (productivity[w][c] * x[w,c])
    for c in components:
        model.addConstr(
            gp.quicksum(productivity[w][c] * x[w, c] for w in workshops) >= z,
            name=f"component_{c+1}_balance"
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