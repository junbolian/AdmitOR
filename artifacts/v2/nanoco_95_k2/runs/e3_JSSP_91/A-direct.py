import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    lots = [0, 1, 2]
    route = {
        0: [(1, "p_0_1"), (0, "p_0_0"), (2, "p_0_2")],
        1: [(1, "p_1_1"), (0, "p_1_0"), (2, "p_1_2")],
        2: [(1, "p_2_1"), (0, "p_2_0"), (2, "p_2_2")],
    }
    num_steps = 3
    steps = list(range(num_steps))
    tools = [0, 1, 2]

    p = {}
    for lot in lots:
        for k, (tool, key) in enumerate(route[lot]):
            p[(lot, k)] = params[key]

    model = pyo.ConcreteModel()

    model.start = pyo.Var(lots, steps, within=pyo.NonNegativeReals)
    model.ord_bin = pyo.Var(lots, steps, within=pyo.Binary)
    model.Cmax = pyo.Var(within=pyo.NonNegativeReals)

    def prec_rule(m, lot, k):
        if k == 0:
            return pyo.Constraint.Skip
        return m.start[lot, k] >= m.start[lot, k - 1] + p[(lot, k - 1)]
    model.prec = pyo.Constraint(lots, steps, rule=prec_rule)

    def cmax_rule(m, lot):
        return m.Cmax >= m.start[lot, num_steps - 1] + p[(lot, num_steps - 1)]
    model.cmax_con = pyo.Constraint(lots, rule=cmax_rule)

    ops_by_tool = {t: [] for t in tools}
    for lot in lots:
        for k, (tool, key) in enumerate(route[lot]):
            ops_by_tool[tool].append((lot, k))

    disj = {}
    ii = 0
    for tool in tools:
        ops = ops_by_tool[tool]
        for a in range(len(ops)):
            for b in range(a + 1, len(ops)):
                disj[ii] = (ops[a], ops[b])
                ii += 1

    model.disj = pyo.Set(initialize=list(disj.keys()))

    M = sum(p.values())

    def disj_rule(m, idx):
        (la, ka), (lb, kb) = disj[idx]
        pa = p[(la, ka)]
        pb = p[(lb, kb)]
        return (m.start[la, ka] + pa <= m.start[lb, kb] + M * m.ord_bin[la, ka],
                m.start[lb, kb] + pb <= m.start[la, ka] + M * (1 - m.ord_bin[la, ka]))
    model.disj_con = pyo.Constraint(model.disj, rule=disj_rule)

    model.obj = pyo.Objective(expr=model.Cmax, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}