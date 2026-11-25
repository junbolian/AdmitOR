import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    investor_rankings = params["investor_rankings"]
    founder_rankings = params["founder_rankings"]

    n_inv = len(investor_rankings)
    n_fnd = len(founder_rankings)

    # Rank lookup: investor_rank[i][j] = position of founder j on investor i's list
    investor_rank = {}
    for i in range(n_inv):
        for pos, j in enumerate(investor_rankings[i]):
            investor_rank[(i, j)] = pos

    # Rank lookup: founder_rank[j][i] = position of investor i on founder j's list
    founder_rank = {}
    for j in range(n_fnd):
        for pos, i in enumerate(founder_rankings[j]):
            founder_rank[(i, j)] = pos

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_inv - 1)
    model.J = pyo.RangeSet(0, n_fnd - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

    # Each investor matched exactly once
    model.inv_assign = pyo.Constraint(
        model.I, rule=lambda m, i: sum(m.x[i, j] for j in m.J) == 1
    )
    # Each founder matched exactly once
    model.fnd_assign = pyo.Constraint(
        model.J, rule=lambda m, j: sum(m.x[i, j] for i in m.I) == 1
    )

    # Stability constraints: for each pair (i, j), forbid blocking pair.
    # (i, j) is unstable if they are not matched, and both strictly prefer
    # each other over their current partners.
    # Equivalent: if x[i,j] = 0, then i must be with some j' that i prefers
    # over j (rank < investor_rank[i][j]), OR j must be with some i' that j
    # prefers over i (rank < founder_rank[i][j]).
    # So: x[i,j] + sum_{j' better than j for i} x[i,j'] + sum_{i' better than i for j} x[i',j] >= 1
    def stab_rule(m, i, j):
        better_for_i = [jj for jj in m.J if investor_rank[(i, jj)] < investor_rank[(i, j)]]
        better_for_j = [ii for ii in m.I if founder_rank[(ii, j)] < founder_rank[(i, j)]]
        return (
            m.x[i, j]
            + sum(m.x[i, jj] for jj in better_for_i)
            + sum(m.x[ii, j] for ii in better_for_j)
            >= 1
        )

    model.stability = pyo.Constraint(model.I, model.J, rule=stab_rule)

    # Objective: minimize total rank-sum deviation
    model.obj = pyo.Objective(
        expr=sum(
            (investor_rank[(i, j)] + founder_rank[(i, j)]) * model.x[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}