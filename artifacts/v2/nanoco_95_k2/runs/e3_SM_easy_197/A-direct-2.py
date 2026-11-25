import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplier_pref_positions = params["supplier_pref_positions"]
    plant_pref_positions = params["plant_pref_positions"]

    n = 7
    suppliers = list(range(n))
    plants = list(range(n))
    pairs = [(s, p) for s in suppliers for p in plants]

    model = pyo.ConcreteModel()

    model.SUP = pyo.Set(initialize=suppliers)
    model.PLT = pyo.Set(initialize=plants)
    model.PAIRS = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.PAIRS, domain=pyo.Binary)

    def match_one_supplier_rule(model, s):
        return sum(model.x[s, p] for p in model.PLT) == 1

    def match_one_plant_rule(model, p):
        return sum(model.x[s, p] for s in model.SUP) == 1

    model.supplier_con = pyo.Constraint(model.SUP, rule=match_one_supplier_rule)
    model.plant_con = pyo.Constraint(model.PLT, rule=match_one_plant_rule)

    def blocking_rule(model, s, p):
        better_plants = sum(
            model.x[s, pp] for pp in model.PLT
            if supplier_pref_positions[s][pp] < supplier_pref_positions[s][p]
        )
        better_suppliers = sum(
            model.x[ss, p] for ss in model.SUP
            if plant_pref_positions[p][ss] < plant_pref_positions[p][s]
        )
        return better_plants + better_suppliers + model.x[s, p] <= 1

    model.stability = pyo.Constraint(model.PAIRS, rule=blocking_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            (supplier_pref_positions[s][p] + plant_pref_positions[p][s]) * model.x[s, p]
            for s, p in model.PAIRS
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}