import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_req = params["protein_requirement"]
    mineral_req = params["mineral_requirement"]
    vitamin_req = params["vitamin_requirement"]
    protein_content = params["protein_content"]
    mineral_content = params["mineral_content"]
    vitamin_content = params["vitamin_content"]
    feed_price = params["feed_price"]

    n_feeds = 5
    feeds = range(n_feeds)

    model = gp.Model("feed_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables: grams of each feed per day
    x = model.addVars(n_feeds, lb=0.0, name="x")

    # Objective: minimize cost (feed_price is in yuan/kg, x is in grams)
    # cost = sum(feed_price[i] / 1000 * x[i]) to convert yuan/kg to yuan/g
    model.setObjective(
        gp.quicksum((feed_price[i] / 1000.0) * x[i] for i in feeds),
        GRB.MINIMIZE
    )

    # Protein constraint
    model.addConstr(
        gp.quicksum(protein_content[i] * x[i] for i in feeds) >= protein_req,
        name="protein"
    )

    # Mineral constraint
    model.addConstr(
        gp.quicksum(mineral_content[i] * x[i] for i in feeds) >= mineral_req,
        name="mineral"
    )

    # Vitamin constraint
    model.addConstr(
        gp.quicksum(vitamin_content[i] * x[i] for i in feeds) >= vitamin_req,
        name="vitamin"
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