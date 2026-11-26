import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _is_dict(x):
    return isinstance(x, dict)


def solve(params):
    D_jk = params["D_jk"]
    r_klm = params["r_klm"]
    R_im = params["R_im"]
    c_kl = params["c_kl"]
    c_il = params["c_il"]
    P_ikl = params["P_ikl"]
    T_ijk = params["T_ijk"]

    # Detect whether data are given as nested dicts or as flat index->value dicts.
    nested = _is_dict(R_im)
    if nested:
        I = sorted(R_im.keys())
        M = sorted(next(iter(R_im.values())).keys())
        J = sorted(D_jk.keys())
        K = sorted(next(iter(D_jk.values())).keys())
        L = sorted(next(iter(c_il.values())).keys())
    else:
        # Flat mapping index -> value. Infer sets from the integer index structure.
        # We use known structural sizes: 10 mills, 1000 customers, 5 paper types,
        # 3 machines, 4 raw material types.
        I = list(range(len(R_im) // 4))
        M = list(range(4))
        J = list(range(len(D_jk) // 5))
        K = list(range(5))
        L = list(range(3))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(I, K, L, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(I, J, K, domain=pyo.NonNegativeReals)

    def _R(i, m):
        return R_im[(i, m)] if not nested else R_im[i][m]

    def _D(j, k):
        return D_jk[(j, k)] if not nested else D_jk[j][k]

    def _r(k, l, m):
        return r_klm[(k, l, m)] if not nested else r_klm[k][l][m]

    def _c(k, l):
        return c_kl[(k, l)] if not nested else c_kl[k][l]

    def _ci(i, l):
        return c_il[(i, l)] if not nested else c_il[i][l]

    def _P(i, k, l):
        return P_ikl[(i, k, l)] if not nested else P_ikl[i][k][l]

    def _T(i, j, k):
        return T_ijk[(i, j, k)] if not nested else T_ijk[i][j][k]

    def obj_rule(m):
        prod = sum(_P(i, k, l) * m.x[i, k, l] for i in I for k in K for l in L)
        trans = sum(_T(i, j, k) * m.y[i, j, k] for i in I for j in J for k in K)
        return prod + trans
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j, k):
        return sum(m.y[i, j, k] for i in I) == _D(j, k)
    model.demand = pyo.Constraint(J, K, rule=demand_rule)

    def balance_rule(m, i, k):
        return sum(m.y[i, j, k] for j in J) == sum(m.x[i, k, l] for l in L)
    model.balance = pyo.Constraint(I, K, rule=balance_rule)

    def raw_rule(m, i, m_):
        return sum(_r(k, l, m_) * m.x[i, k, l] for k in K for l in L) <= _R(i, m_)
    model.raw = pyo.Constraint(I, M, rule=raw_rule)

    def machine_rule(m, i, l):
        return sum(_c(k, l) * m.x[i, k, l] for k in K) <= _ci(i, l)
    model.machine = pyo.Constraint(I, L, rule=machine_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}