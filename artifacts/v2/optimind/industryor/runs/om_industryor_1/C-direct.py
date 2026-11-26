import gurobipy as gp
from gurobipy import GRB

def solve(params):
    a1 = params["a1"]
    a2 = params["a2"]
    pilot_yield = params["pilot_yield_per_training_jet"]
    n = params["n"]

    total_jets = a1 + a2  # jets delivered each year

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x[t]: combat jets in year t (1-indexed, stored 0-indexed)
    # y[t]: training jets in year t
    # p[t]: available trained pilots at start of year t
    # fleet[t]: total aircraft in fleet at start of year t (available for combat or training)

    x = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="x")
    y = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="y")
    p = model.addVars(n + 1, vtype=GRB.INTEGER, lb=0, name="p")  # p[0] = 0 (start), p[t] after year t-1 training
    fleet = model.addVars(n + 1, vtype=GRB.INTEGER, lb=0, name="fleet")  # fleet[t]: jets available at start of year t

    # Objective: maximize cumulative operational combat jet-years
    model.setObjective(gp.quicksum(x[t] for t in range(n)), GRB.MAXIMIZE)

    # Initial conditions: no aircraft, no pilots
    model.addConstr(p[0] == 0, name="init_pilots")
    model.addConstr(fleet[0] == 0, name="init_fleet")

    for t in range(n):
        # Total jets available this year = fleet carried over + new deliveries
        # x[t] + y[t] = total jets available this year
        model.addConstr(x[t] + y[t] == fleet[t] + total_jets, name=f"jet_balance_{t}")

        # Combat jets cannot exceed available trained pilots
        model.addConstr(x[t] <= p[t], name=f"pilot_limit_{t}")

        # x and y must be non-negative (already enforced by lb=0)
        # Fleet for next year: training jets carry over as they can be reassigned,
        # combat jets are consumed (operational), training jets persist in fleet
        # Actually: all jets persist in fleet. Combat jets are operational this year,
        # training jets produce pilots. Both remain in fleet next year.
        # Fleet next year = fleet this year + new deliveries = x[t] + y[t]
        model.addConstr(fleet[t + 1] == fleet[t] + total_jets, name=f"fleet_update_{t}")

        # Pilots for next year = current pilots - pilots used in combat + new pilots from training
        # Pilots used in combat = x[t] (each combat jet uses one pilot)
        # New pilots from training = pilot_yield * y[t]
        model.addConstr(
            p[t + 1] == p[t] - x[t] + pilot_yield * y[t],
            name=f"pilot_update_{t}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}