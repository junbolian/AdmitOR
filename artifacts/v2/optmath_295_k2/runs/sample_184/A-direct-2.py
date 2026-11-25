import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_orig = 4
    n_dest = 5
    n_prod = 2

    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    def get_nested(data, *idx):
        for i in idx:
            data = data[i]
        return data

    def get_flat(data, flat_idx):
        return data[flat_idx]

    def fetch(data, idx_tuple, flat_idx):
        try:
            return get_nested(data, *idx_tuple)
        except (TypeError, IndexError):
            return get_flat(data, flat_idx)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_orig - 1)
    model.J = pyo.RangeSet(0, n_dest - 1)
    model.K = pyo.RangeSet(0, n_prod - 1)

    def s_init(B, i, k):
        return fetch(supply, (i, k), i * n_prod + k)

    def d_init(B, j, k):
        return fetch(demand, (j, k), j * n_prod + k)

    def c_init(B, i, j, k):
        return fetch(cost, (i, j, k), (i * n_dest + j) * n_prod + k)

    def cap_init(B, i, j):
        return fetch(capacity, (i, j), i * n_dest + j)

    model.supply = pyo.Param(model.I, model.K, initialize=s_init)
    model.demand = pyo.Param(model.J, model.K, initialize=d_init)
    model.cost = pyo.Param(model.I, model.J, model.K, initialize=c_init)
    model.cap = pyo.Param(model.I, model.J, initialize=cap_init)

    model.x = pyo.Var(model.I, model.J, model.K, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(m.cost[i, j, k] * m.x[i, j, k]
                   for i in m.I for j in m.J for k in m.K)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i, k):
        return sum(m.x[i, j, k] for j in m.J) == m.supply[i, k]

    model.supply_con = pyo.Constraint(model.I, model.K, rule=supply_rule)

    def demand_rule(m, j, k):
        return sum(m.x[i, j, k] for i in m.I) == m.demand[j, k]

    model.demand_con = pyo.Constraint(model.J, model.K, rule=demand_rule)

    def cap_rule(m, i, j):
        return sum(m.x[i, j, k] for k in m.K) <= m.cap[i, j]

    model.cap_con = pyo.Constraint(model.I, model.J, rule=cap_rule)

    solver = Highs()
    solver.config.load_solution = True
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}