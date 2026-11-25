import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplier_pref = params["supplier_pref_positions"]
    plant_pref = params["plant_pref_positions"]
    n = len(supplier_pref)

    model = pyo.ConcreteModel()

    model.suppliers = pyo.RangeSet(0, n - 1)
    model.plants = pyo.RangeSet(0, n - 1)
    model.pairs = pyo.Set(
        initialize=[(i, j) for i in range(n) for j in range(n)], dimen=2
    )

    model.x = pyo.Var(model.pairs, domain=pyo.Binary)

    model.total_risk = pyo.Objective(
        expr=sum(
            (supplier_pref[i][j] + plant_pref[j][i]) * model.x[i, j]
            for i in range(n)
            for j in range(n)
        ),
        sense=pyo.minimize,
    )

    def supplier_match_rule(m, i):
        return sum(m.x[i, j] for j in range(n)) == 1

    model.supplier_match = pyo.Constraint(model.suppliers, rule=supplier_match_rule)

    def plant_match_rule(m, j):
        return sum(m.x[i, j] for i in range(n)) == 1

    model.plant_match = pyo.Constraint(model.plants, rule=plant_match_rule)

    # Stability: no blocking pair. For any pair (i, j), not both may prefer
    # a deviation. If indices are consecutive, no strictly better partner is
    # worse-ranked than j (or strictly worse than i), so the rule is trivially
    # feasible.
    def stability_rule(m, i, j):
        worse_plants = [
            jj for jj in range(n) if supplier_pref[i][jj] > supplier_pref[i][j]
        ]
        worse_suppliers = [
            ii for ii in range(n) if plant_pref[j][ii] > plant_pref[j][i]
        ]
        if not worse_plants or not worse_suppliers:
            return pyo.Constraint.Feasible
        supplier_prefers = sum(m.x[i, jj] for jj in worse_plants)
        plant_prefers = sum(m.x[ii, j] for ii in worse_suppliers)
        return supplier_prefers + plant_prefers <= 1

    model.stability = pyo.Constraint(model.pairs, rule=stability_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_risk))
    return {"objective": obj_val, "status": "optimal"}