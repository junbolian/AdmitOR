import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_nodes"])
    nodes = list(range(n))

    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def cap(i, j):
        return float(params[f"capacity_{i}_{j}"])

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def cap_rule(md, i, j):
        return md.flow[i, j] <= cap(i, j)

    model.cap_con = pyo.Constraint(model.arcs, rule=cap_rule)

    # Flow conservation: source (0) and sink (n-1) have no conservation,
    # all intermediate nodes balance inflow = outflow.
    source = 0
    sink = n - 1
    intermediate = [k for k in nodes if k != source and k != sink]

    def balance_rule(md, k):
        inflow = sum(md.flow[i, k] for i in nodes if i != k)
        outflow = sum(md.flow[k, j] for j in nodes if j != k)
        return inflow == outflow

    model.balance_con = pyo.Constraint(intermediate, rule=balance_rule)

    def obj_rule(md):
        return sum(md.flow[source, j] for j in nodes if j != source)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}