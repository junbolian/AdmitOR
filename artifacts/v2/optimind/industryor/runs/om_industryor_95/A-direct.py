import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sulfur_A = params["sulfur_A"]
    sulfur_B = params["sulfur_B"]
    sulfur_C = params["sulfur_C"]
    sulfur_D = params["sulfur_D"]
    price_A = params["price_A"]
    price_B = params["price_B"]
    price_C = params["price_C"]
    price_D = params["price_D"]
    sell_A = params["sell_A"]
    sell_B = params["sell_B"]
    max_sulfur_A = params["max_sulfur_A"]
    max_sulfur_B = params["max_sulfur_B"]
    supply_D = params["supply_D"]
    demand_A = params["demand_A"]
    demand_B = params["demand_B"]

    model = pyo.ConcreteModel()

    # Raw material quantities fed to the mixer
    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)
    model.xC = pyo.Var(domain=pyo.NonNegativeReals)
    model.xD = pyo.Var(domain=pyo.NonNegativeReals)

    # Product quantities
    model.prodA = pyo.Var(domain=pyo.NonNegativeReals)
    model.prodB = pyo.Var(domain=pyo.NonNegativeReals)

    # Total mass balance: all raw materials consumed into products
    model.mass_balance = pyo.Constraint(
        expr=model.xA + model.xB + model.xC + model.xD == model.prodA + model.prodB
    )

    # Supply limit for D
    model.supply_D_con = pyo.Constraint(expr=model.xD <= supply_D)

    # Demand caps
    model.demand_A_con = pyo.Constraint(expr=model.prodA <= demand_A)
    model.demand_B_con = pyo.Constraint(expr=model.prodB <= demand_B)

    # Sulfur balance: total sulfur in raw materials must be distributed
    # to products respecting their sulfur limits.
    # Products A and B combined consume all sulfur S_total.
    # Feasibility of quality requires:
    #   sulfur endorsed to A <= max_sulfur_A * prodA
    #   sulfur to B <= max_sulfur_B * prodB
    # Since C is added after mixing A,B,D, C can go to either product.
    # Total sulfur constraint per product:
    model.sulfur_A_con = pyo.Constraint(
        expr=sulfur_A * model.xA + sulfur_B * model.xB
        + sulfur_C * model.xC + sulfur_D * model.xD
        <= max_sulfur_A * model.prodA + max_sulfur_B * model.prodB
    )

    # Profit: revenue - purchase cost
    model.profit = pyo.Expression(
        expr=sell_A * model.prodA + sell_B * model.prodB
        - (price_A * model.xA + price_B * model.xB
           + price_C * model.xC + price_D * model.xD)
    )

    model.obj = pyo.Objective(expr=model.profit, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}