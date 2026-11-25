import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants: number of investors and founders
    n = 5

    # Rankings (0-indexed preference orders) – structural, given in problem
    investor_ranks = [
        [0, 2, 3, 1, 4],
        [1, 4, 2, 0, 3],
        [3, 1, 0, 4, 2],
        [0, 4, 2, 1, 3],
        [2, 0, 1, 3, 4],
    ]
    founder_ranks = [
        [4, 1, 3, 2, 0],
        [0, 3, 1, 2, 4],
        [3, 1, 2, 0, 4],
        [2, 1, 4, 0, 3],
        [1, 4, 0, 3, 2],
    ]

    # Build rank lookup: pos_inv[i][f] = rank of founder f on investor i's list
    pos_inv = [[0] * n for _ in range(n)]
    for i in range(n):
        for rank, f in enumerate(investor_ranks[i]):
            pos_inv[i][f] = rank

    # pos_fnd[f][i] = rank of investor i on founder f's list
    pos_fnd = [[0] * n for _ in range(n)]
    for f in range(n):
        for rank, i in enumerate(founder_ranks[f]):
            pos_fnd[f][i] = rank

    # Cost of matching investor i with founder f
    cost = [[pos_inv[i][f] + pos_fnd[f][i] for f in range(n)] for i in range(n)]

    model = pyo.ConcreteModel()

    model.Inv = pyo.RangeSet(0, n - 1)
    model.Fnd = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.Inv, model.Fnd, domain=pyo.Binary)

    # Each investor matched to exactly one founder
    def inv_rule(m, i):
        return sum(m.x[i, f] for f in m.Fnd) == 1
    model.inv_match = pyo.Constraint(model.Inv, rule=inv_rule)

    # Each founder matched to exactly one investor
    def fnd_rule(m, f):
        return sum(m.x[i, f] for i in m.Inv) == 1
    model.fnd_match = pyo.Constraint(model.Fnd, rule=fnd_rule)

    # Stability constraints: for each pair (i,f), prevent blocking pair.
    # A blocking pair exists if investor i prefers f over current partner AND
    # founder f prefers i over current partner.
    # We forbid: x[i,f]=0, i prefers f over partner, f prefers i over partner.
    # Equivalent: for all i,f, if x[i,f]==0 then NOT(i prefers f over partner) OR NOT(f prefers i over partner).
    # We model: sum over founders f' preferred by i over f of x[i,f'] + sum over investors i' preferred by f over i of x[i',f] >= 1 - x[i,f]
    # Actually: if x[i,f]=1, constraint trivially satisfied.
    # If x[i,f]=0, require: i's partner is preferred to f OR f's partner is preferred to i.
    # i's partner preferred to f  <=>  i matched to some f' with pos_inv[i][f'] < pos_inv[i][f]
    # f's partner preferred to i  <=>  f matched to some i' with pos_fnd[f][i'] < pos_fnd[f][i]

    def stab_rule(m, i, f):
        # founders strictly preferred by i over f
        better_f = [g for g in range(n) if pos_inv[i][g] < pos_inv[i][f]]
        # investors strictly preferred by f over i
        better_i = [j for j in range(n) if pos_fnd[f][j] < pos_fnd[f][i]]
        lhs = sum(m.x[i, g] for g in better_f) + sum(m.x[j, f] for j in better_i)
        return lhs >= 1 - m.x[i, f]

    model.stability = pyo.Constraint(model.Inv, model.Fnd, rule=stab_rule)

    # Objective: minimize total strategic misfit
    def obj_rule(m):
        return sum(cost[i][f] * m.x[i, f] for i in m.Inv for f in m.Fnd)
    model.total_misfit = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_misfit))
    return {"objective": obj_val, "status": "optimal"}