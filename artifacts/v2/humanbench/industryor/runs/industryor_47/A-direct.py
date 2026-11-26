import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_I = params["demand_I"]
    demand_II = params["demand_II"]
    cost_I = params["cost_I"]
    cost_II = params["cost_II"]
    production_capacity = params["production_capacity"]
    warehouse_capacity = params["warehouse_capacity"]
    space_I = params["space_I"]
    space_II = params["space_II"]
    own_storage_cost = params["own_storage_cost"]
    external_storage_cost = params["external_storage_cost"]

    T = list(range(12))

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=T, ordered=True)

    model.xI = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.xII = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.ext = pyo.Var(model.T, within=pyo.NonNegativeReals)

    def prod_cap_rule(m, t):
        return m.xI[t] + m.xII[t] <= production_capacity
    model.prod_cap = pyo.Constraint(model.T, rule=prod_cap_rule)

    def demand_I_rule(m, t):
        return m.xI[t] >= demand_I[t]
    model.demand_I_c = pyo.Constraint(model.T, rule=demand_I_rule)

    def demand_II_rule(m, t):
        return m.xII[t] >= demand_II[t]
    model.demand_II_c = pyo.Constraint(model.T, rule=demand_II_rule)

    # Storage: only the portion within own warehouse capacity incurs own_storage_cost,
    # any overflow is rented externally at external_storage_cost.
    def storage_rule(m, t):
        used = space_I * m.xI[t] + space_II * m.xII[t]
        return used <= warehouse_capacity + m.ext[t]
    model.storage_c = pyo.Constraint(model.T, rule=storage_rule)

    def obj_rule(m):
        return sum(
            cost_I[t] * m.xI[t]
            + cost_II[t] * m.xII[t]
            + own_storage_cost * (space_I * m.xI[t] + space_II * m.xII[t])
            + external_storage_cost * m.ext[t]
            for t in m.T
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}