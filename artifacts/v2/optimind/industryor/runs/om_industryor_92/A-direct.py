import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price_gas_I = params["price_gas_I"]
    price_gas_II = params["price_gas_II"]
    min_prop_A_I = params["min_prop_A_I"]
    min_prop_A_II = params["min_prop_A_II"]
    inventory_A = params["inventory_A"]
    inventory_B = params["inventory_B"]
    max_purchase_A = params["max_purchase_A"]
    price_tier1 = params["price_tier1"]
    tier1_limit = params["tier1_limit"]
    price_tier2 = params["price_tier2"]
    tier2_limit = params["tier2_limit"]
    price_tier3 = params["price_tier3"]

    model = pyo.ConcreteModel()

    # Decision variables
    # Quantities of crude A and B used in gasoline I and II
    model.aI = pyo.Var(domain=pyo.NonNegativeReals)
    model.bI = pyo.Var(domain=pyo.NonNegativeReals)
    model.aII = pyo.Var(domain=pyo.NonNegativeReals)
    model.bII = pyo.Var(domain=pyo.NonNegativeReals)

    # Purchased crude A in each price tier
    model.p1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.p2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.p3 = pyo.Var(domain=pyo.NonNegativeReals)

    # Tier limits
    model.p1.setub(tier1_limit)
    model.p2.setub(tier2_limit)

    # Constraint: total purchased <= max_purchase_A
    model.max_purchase = pyo.Constraint(
        expr=model.p1 + model.p2 + model.p3 <= max_purchase_A
    )

    # Crude A availability: usage <= inventory_A + purchases
    model.avail_A = pyo.Constraint(
        expr=model.aI + model.aII <= inventory_A + model.p1 + model.p2 + model.p3
    )

    # Crude B availability
    model.avail_B = pyo.Constraint(expr=model.bI + model.bII <= inventory_B)

    # Minimum proportion of crude A in gasoline I:
    # aI >= min_prop_A_I * (aI + bI)
    model.prop_I = pyo.Constraint(
        expr=model.aI >= min_prop_A_I * (model.aI + model.bI)
    )

    # Minimum proportion of crude A in gasoline II
    model.prop_II = pyo.Constraint(
        expr=model.aII >= min_prop_A_II * (model.aII + model.bII)
    )

    # Objective: revenue - purchase cost
    model.profit = pyo.Expression(
        expr=price_gas_I * (model.aI + model.bI)
        + price_gas_II * (model.aII + model.bII)
        - price_tier1 * model.p1
        - price_tier2 * model.p2
        - price_tier3 * model.p3
    )

    model.obj = pyo.Objective(expr=model.profit, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}