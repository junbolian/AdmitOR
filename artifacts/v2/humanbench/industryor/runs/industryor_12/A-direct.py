import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Indexed sets for the tiered profitability structure (piecewise segments)
    # For each product, list of (segment_index, lower_breakpoint_key, upper_breakpoint_key, profit_key)
    # Segment widths: A -> [0,B1],[B1,B2],[B2,B3],[B3,inf); B -> [0,B1],[B1,B2],[B2,inf); C -> [0,B1],[B1,inf)
    model.segA = pyo.Set(initialize=[1, 2, 3, 4])
    model.segB = pyo.Set(initialize=[1, 2, 3])
    model.segC = pyo.Set(initialize=[1, 2])

    # Decision variables: units produced/sold per product
    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)
    model.xC = pyo.Var(domain=pyo.NonNegativeReals)

    # Segment variables (units sold within each tier)
    model.yA = pyo.Var(model.segA, domain=pyo.NonNegativeReals)
    model.yB = pyo.Var(model.segB, domain=pyo.NonNegativeReals)
    model.yC = pyo.Var(model.segC, domain=pyo.NonNegativeReals)

    # Bounds on segment quantities from breakpoints
    bpA1 = params["breakpoint_A_1"]
    bpA2 = params["breakpoint_A_2"]
    bpA3 = params["breakpoint_A_3"]
    bpB1 = params["breakpoint_B_1"]
    bpB2 = params["breakpoint_B_2"]
    bpC1 = params["breakpoint_C_1"]

    model.capA1 = pyo.Constraint(expr=model.yA[1] <= bpA1)
    model.capA2 = pyo.Constraint(expr=model.yA[2] <= bpA2 - bpA1)
    model.capA3 = pyo.Constraint(expr=model.yA[3] <= bpA3 - bpA2)
    # segment 4 unbounded above

    model.capB1 = pyo.Constraint(expr=model.yB[1] <= bpB1)
    model.capB2 = pyo.Constraint(expr=model.yB[2] <= bpB2 - bpB1)
    # segment 3 unbounded above

    model.capC1 = pyo.Constraint(expr=model.yC[1] <= bpC1)
    # segment 2 unbounded above

    # Total production equals sum of segment quantities
    model.linkA = pyo.Constraint(expr=model.xA == sum(model.yA[k] for k in model.segA))
    model.linkB = pyo.Constraint(expr=model.xB == sum(model.yB[k] for k in model.segB))
    model.linkC = pyo.Constraint(expr=model.xC == sum(model.yC[k] for k in model.segC))

    # Resource constraints
    model.tech = pyo.Constraint(
        expr=params["tech_prep_A"] * model.xA
        + params["tech_prep_B"] * model.xB
        + params["tech_prep_C"] * model.xC
        <= params["capacity_tech_prep"]
    )
    model.labor = pyo.Constraint(
        expr=params["labor_A"] * model.xA
        + params["labor_B"] * model.xB
        + params["labor_C"] * model.xC
        <= params["capacity_labor"]
    )
    model.material = pyo.Constraint(
        expr=params["material_A"] * model.xA
        + params["material_B"] * model.xB
        + params["material_C"] * model.xC
        <= params["capacity_material"]
    )

    # Objective: sum of profit per segment times segment quantity
    profitA = {
        1: params["profit_A_tier1"],
        2: params["profit_A_tier2"],
        3: params["profit_A_tier3"],
        4: params["profit_A_tier4"],
    }
    profitB = {
        1: params["profit_B_tier1"],
        2: params["profit_B_tier2"],
        3: params["profit_B_tier3"],
    }
    profitC = {
        1: params["profit_C_tier1"],
        2: params["profit_C_tier2"],
    }

    model.profit = pyo.Expression(
        expr=sum(profitA[k] * model.yA[k] for k in model.segA)
        + sum(profitB[k] * model.yB[k] for k in model.segB)
        + sum(profitC[k] * model.yC[k] for k in model.segC)
    )

    model.obj = pyo.Objective(expr=model.profit, sense=pyo.maximize)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}