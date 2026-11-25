import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    N = list(range(6))
    arcs = [(i, j) for i in N for j in N if i != j]

    model.arcs = pyo.Set(dimen=2, initialize=arcs)
    model.nodes = pyo.Set(initialize=N)

    b = {i: params["supply_demand"][i] for i in N}

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.open = pyo.Var(model.arcs, domain=pyo.Binary)

    fixed_data = {(i, j): params[f"fixed_cost_{i}_{j}"] for (i, j) in arcs}
    var_data = {(i, j): params[f"variable_cost_{i}_{j}"] for (i, j) in arcs}
    cap_data = {(i, j): params[f"capacity_{i}_{j}"] for (i, j) in arcs}

    model.fixed_cost = pyo.Param(model.arcs, initialize=fixed_data)
    model.var_cost = pyo.Param(model.arcs, initialize=var_data)
    model.cap = pyo.Param(model.arcs, initialize=cap_data)

    def flow_balance(mdl, i):
        return sum(mdl.flow[i, j] for j in N if j != i) - \
               sum(mdl.flow[j, i] for j in N if j != i) == b[i]

    model.balance = pyo.Constraint(model.nodes, rule=flow_balance)

    def cap_link(mdl, i, j):
        return mdl.flow[i, j] <= mdl.cap[i, j] * mdl.open[i, j]

    model.cap_link = pyo.Constraint(model.arcs, rule=cap_link)

    def obj_rule(mdl):
        return sum(mdl.fixed_cost[i, j] * mdl.open[i, j] +
                   mdl.var_cost[i, j] * mdl.flow[i, j] for (i, j) in mdl.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}