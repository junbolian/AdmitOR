import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Try single-letter keys first, fall back to descriptive keys
    def get(short, *alternatives):
        for key in (short,) + alternatives:
            if key in params:
                return params[key]
        raise KeyError(f"None of {(short,) + alternatives} found in params: {list(params.keys())}")

    # Read parameters - support both single-letter and descriptive key names
    a = params.get("a", params.get("hours_method1", params.get("a")))
    
    # Inspect actual keys and map accordingly
    keys = list(params.keys())
    
    # Build a normalized mapping based on position if keys are descriptive
    # The params spec says: a, b, m, n, k, d, c
    # Try direct access first
    if "a" in params:
        a = params["a"]
        b = params["b"]
        m = params["m"]
        n = params["n"]
        k = params["k"]
        d = params["d"]
        c = params["c"]
    else:
        # Map by the meaning order: hours_method1, hours_method2, fuel_method1, fuel_method2, tons_per_furnace, min_steel, total_hours
        # or whatever descriptive names are used - use positional fallback
        vals = list(params.values())
        # Try common descriptive names
        a = params.get("hours_per_furnace_method1", params.get("a_hours", vals[0]))
        b = params.get("hours_per_furnace_method2", params.get("b_hours", vals[1]))
        m = params.get("fuel_cost_method1", params.get("m_cost", vals[2]))
        n = params.get("fuel_cost_method2", params.get("n_cost", vals[3]))
        k = params.get("tons_per_furnace", params.get("k_tons", vals[4]))
        d = params.get("min_steel", params.get("d_demand", vals[5]))
        c = params.get("total_hours", params.get("c_hours", vals[6]))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x1 = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x1")
    x2 = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x2")

    model.setObjective(m * x1 + n * x2, GRB.MINIMIZE)

    model.addConstr(k * x1 + k * x2 >= d, name="steel_production")
    model.addConstr(a * x1 + b * x2 <= c, name="hours_limit")

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