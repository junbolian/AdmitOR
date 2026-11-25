import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["locker_fixed_costs"]
    capacities = params["locker_capacities"]
    demands = params["customer_demands"]
    cost_mat = params["delivery_cost_matrix"]

    num_l = int(params["num_lockers"])
    num_c = int(params["num_customers"])

    lockers = list(range(num_l))
    customers = list(range(num_c))

    model = pyo.ConcreteModel()

    model.L = pyo.Set(initialize=lockers, ordered=True)
    model.C = pyo.Set(initialize=customers, ordered=True)

    model.fixed_cost = pyo.Param(model.L, initialize={l: fixed_costs[l] for l in lockers})
    model.capacity = pyo.Param(model.L, initialize={l: capacities[l] for l in lockers})
    model.demand = pyo.Param(model.C, initialize={c: demands[c] for c in customers})

    model.delivery_cost = pyo.Param(
        model.C, model.L,
        initialize={(c, l): cost_mat[c][l] for c in customers for l in lockers}
    )

    model.y = pyo.Var(model.L, domain=pyo.Binary)
    model.x = pyo.Var(model.C, model.L, domain=pyo.Binary)

    def _obj_rule(m):
        return sum(m.fixed_cost[l] * m.y[l] for l in m.L) + \
               sum(m.delivery_cost[c, l] * m.x[c, l] for c in m.C for l in m.L)

    model.total_cost = pyo.Objective(rule=_obj_rule, sense=pyo.minimize)

    def _assign_rule(m, c):
        return sum(m.x[c, l] for l in m.L) == 1

    model.assign_one = pyo.Constraint(model.C, rule=_assign_rule)

    def _cap_rule(m, l):
        return sum(m.demand[c] * m.x[c, l] for c in m.C) <= m.capacity[l] * m.y[l]

    model.capacity_limit = pyo.Constraint(model.L, rule=_cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}