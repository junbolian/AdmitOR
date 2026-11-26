import gurobipy as gp
from gurobipy import GRB

def solve(params):
    requirements = params["requirements"]  # list of 7 values, Mon-Sun

    # Days: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    # x[i] = number of employees starting their 5-day shift on day i
    # Shift starting day i works days i, i+1, i+2, i+3, i+4 (mod 7)

    model = gp.Model("post_office")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i] = employees starting on day i
    x = model.addVars(7, vtype=GRB.CONTINUOUS, lb=0, name="x")

    # Objective: minimize total employees hired
    model.setObjective(gp.quicksum(x[i] for i in range(7)), GRB.MINIMIZE)

    # Coverage constraints: for each day d, sum of x[i] where day d is in shift i
    # Shift starting day i covers days i, i+1, i+2, i+3, i+4 (mod 7)
    # Day d is covered by shift i if d in {i, i+1, i+2, i+3, i+4} mod 7
    # Equivalently, shift i covers day d if (d - i) mod 7 in {0,1,2,3,4}
    for d in range(7):
        covering = [i for i in range(7) if (d - i) % 7 in range(5)]
        model.addConstr(
            gp.quicksum(x[i] for i in covering) >= requirements[d],
            name=f"day_{d}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}