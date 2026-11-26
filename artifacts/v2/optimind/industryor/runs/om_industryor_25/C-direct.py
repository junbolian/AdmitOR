import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # params values may be lists (positional) or dicts; normalize to dicts
    machines = ["A1", "A2", "B1", "B2", "B3"]
    products = ["I", "II", "III"]

    def to_dict(val, keys):
        if isinstance(val, dict):
            return val
        # assume list/tuple in same order as keys, skip None/missing entries
        return {k: v for k, v in zip(keys, val) if v is not None}

    pt_I_raw   = params["processing_time_I"]
    pt_II_raw  = params["processing_time_II"]
    pt_III_raw = params["processing_time_III"]
    eff_raw    = params["effective_hours"]
    op_raw     = params["operating_cost_full"]
    rm_raw     = params["raw_material_cost"]
    up_raw     = params["unit_price"]

    processing_time_I   = to_dict(pt_I_raw,   machines)   # A1,A2,B1,B2,B3
    processing_time_II  = to_dict(pt_II_raw,  ["A1","A2","B1"])
    processing_time_III = to_dict(pt_III_raw, ["A2","B2"])
    effective_hours     = to_dict(eff_raw,    machines)
    operating_cost_full = to_dict(op_raw,     machines)
    raw_material_cost   = to_dict(rm_raw,     products)
    unit_price          = to_dict(up_raw,     products)

    model = gp.Model("factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of each product routed through each eligible machine
    # Product I on A process
    xI_A1 = model.addVar(lb=0, name="xI_A1")
    xI_A2 = model.addVar(lb=0, name="xI_A2")
    # Product I on B process
    xI_B1 = model.addVar(lb=0, name="xI_B1")
    xI_B2 = model.addVar(lb=0, name="xI_B2")
    xI_B3 = model.addVar(lb=0, name="xI_B3")

    # Product II on A process
    xII_A1 = model.addVar(lb=0, name="xII_A1")
    xII_A2 = model.addVar(lb=0, name="xII_A2")
    # Product II on B process (B1 only)
    xII_B1 = model.addVar(lb=0, name="xII_B1")

    # Product III on A process (A2 only)
    xIII_A2 = model.addVar(lb=0, name="xIII_A2")
    # Product III on B process (B2 only)
    xIII_B2 = model.addVar(lb=0, name="xIII_B2")

    model.update()

    # Flow balance: units entering process A must equal units entering process B for each product
    model.addConstr(xI_A1 + xI_A2 == xI_B1 + xI_B2 + xI_B3, name="balance_I")
    model.addConstr(xII_A1 + xII_A2 == xII_B1,               name="balance_II")
    model.addConstr(xIII_A2 == xIII_B2,                       name="balance_III")

    # Machine capacity constraints
    model.addConstr(
        processing_time_I["A1"] * xI_A1 + processing_time_II["A1"] * xII_A1
        <= effective_hours["A1"],
        name="cap_A1"
    )
    model.addConstr(
        processing_time_I["A2"] * xI_A2 + processing_time_II["A2"] * xII_A2
        + processing_time_III["A2"] * xIII_A2
        <= effective_hours["A2"],
        name="cap_A2"
    )
    model.addConstr(
        processing_time_I["B1"] * xI_B1 + processing_time_II["B1"] * xII_B1
        <= effective_hours["B1"],
        name="cap_B1"
    )
    model.addConstr(
        processing_time_I["B2"] * xI_B2 + processing_time_III["B2"] * xIII_B2
        <= effective_hours["B2"],
        name="cap_B2"
    )
    model.addConstr(
        processing_time_I["B3"] * xI_B3
        <= effective_hours["B3"],
        name="cap_B3"
    )

    # Operating cost rate per machine-hour used = full_capacity_cost / effective_hours
    op_cost_rate = {m: operating_cost_full[m] / effective_hours[m] for m in machines}

    hours_A1 = processing_time_I["A1"] * xI_A1 + processing_time_II["A1"] * xII_A1
    hours_A2 = (processing_time_I["A2"] * xI_A2 + processing_time_II["A2"] * xII_A2
                + processing_time_III["A2"] * xIII_A2)
    hours_B1 = processing_time_I["B1"] * xI_B1 + processing_time_II["B1"] * xII_B1
    hours_B2 = processing_time_I["B2"] * xI_B2 + processing_time_III["B2"] * xIII_B2
    hours_B3 = processing_time_I["B3"] * xI_B3

    total_operating_cost = (
        op_cost_rate["A1"] * hours_A1 +
        op_cost_rate["A2"] * hours_A2 +
        op_cost_rate["B1"] * hours_B1 +
        op_cost_rate["B2"] * hours_B2 +
        op_cost_rate["B3"] * hours_B3
    )

    # Total units of each product produced
    total_I   = xI_A1 + xI_A2
    total_II  = xII_A1 + xII_A2
    total_III = xIII_A2

    revenue  = (unit_price["I"] * total_I
                + unit_price["II"] * total_II
                + unit_price["III"] * total_III)

    raw_cost = (raw_material_cost["I"] * total_I
                + raw_material_cost["II"] * total_II
                + raw_material_cost["III"] * total_III)

    profit = revenue - raw_cost - total_operating_cost

    model.setObjective(profit, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}