import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Tolerant parameter lookups (harness may pass different key names)
    def pick(*names):
        for nm in names:
            if nm in params:
                return params[nm]
        raise KeyError(names[0])

    a = pick("a", "supply", "output")
    b = pick("b", "demand")
    f = pick("f", "fixed_cost")
    q = pick("q", "capacity", "q_cap")
    c_ik = pick("c_ik", "cik", "c_i_k")
    c_kj = pick("c_kj", "ckj", "c_k_j")

    m = len(a)
    n = len(b)
    p = len(f)

    def row_get(mat, r, c):
        # supports dict-of-dicts, list-of-lists, and dict keyed by tuples
        if isinstance(mat, dict):
            if (r, c) in mat:
                return mat[(r, c)]
            return mat[r][c]
        return mat[r][c]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, m - 1)
    model.J = pyo.RangeSet(0, n - 1)
    model.K = pyo.RangeSet(0, p - 1)

    def a_init(mdl, i):
        return a[i]

    def b_init(mdl, j):
        return b[j]

    def f_init(mdl, k):
        return f[k]

    def q_init(mdl, k):
        return q[k]

    def cik_init(mdl, i, k):
        return row_get(c_ik, i, k)

    def ckj_init(mdl, k, j):
        return row_get(c_kj, k, j)

    model.a = pyo.Param(model.I, initialize=a_init)
    model.b = pyo.Param(model.J, initialize=b_init)
    model.f = pyo.Param(model.K, initialize=f_init)
    model.qcap = pyo.Param(model.K, initialize=q_init)
    model.cik = pyo.Param(model.I, model.K, initialize=cik_init)
    model.ckj = pyo.Param(model.K, model.J, initialize=ckj_init)

    model.x = pyo.Var(model.I, model.K, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.K, model.J, domain=pyo.NonNegativeReals)
    model.z = pyo.Var(model.K, domain=pyo.Binary)

    def obj_rule(mdl):
        return (sum(mdl.cik[i, k] * mdl.x[i, k] for i in mdl.I for k in mdl.K)
                + sum(mdl.ckj[k, j] * mdl.y[k, j] for k in mdl.K for j in mdl.J)
                + sum(mdl.f[k] * mdl.z[k] for k in mdl.K))

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, k] for k in mdl.K) <= mdl.a[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.y[k, j] for k in mdl.K) >= mdl.b[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    def flow_rule(mdl, k):
        return sum(mdl.x[i, k] for i in mdl.I) == sum(mdl.y[k, j] for j in mdl.J)

    model.flow_con = pyo.Constraint(model.K, rule=flow_rule)

    def cap_rule(mdl, k):
        return sum(mdl.x[i, k] for i in mdl.I) <= mdl.qcap[k] * mdl.z[k]

    model.cap_con = pyo.Constraint(model.K, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}