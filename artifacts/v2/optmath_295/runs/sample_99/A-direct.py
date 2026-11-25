import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    net_demand = params["net_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]
    num_nodes = int(params["num_nodes"])

    arcs = [(i, j) for i in range(num_nodes) for j in range(num_nodes) if i != j]
    arc_index = {a: k for k, a in enumerate(arcs)}

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.build = pyo.Var(model.arcs, domain=pyo.Binary)

    def _fixed(m):
        return sum(fixed_cost[k] * m.build[a] for k, a in enumerate(arcs))

    def _variable(m):
        return sum(variable_cost[k] * m.flow[a] for k, a in enumerate(arcs))

    model.fixed_obj = pyo.Expression(rule=_fixed)
    model.var_obj = pyo.Expression(rule=_variable)
    model.total_obj = pyo.Objective(expr=model.fixed_obj + model.var_obj, sense=pyo.minimize)

    def _cap(m, i, j):
        idx = arc_index[(i, j)]
        return m.flow[i, j] <= capacity[idx] * m.build[i, j]

    model.cap_con = pyo.Constraint(model.arcs, rule=_cap)

    def _balance(m, i):
        inflow = sum(m.flow[a] for a in arcs if a[1] == i)
        outflow = sum(m.flow[a] for a in arcs if a[0] == i)
        return inflow - outflow == net_demand[i]

    model.balance_con = pyo.Constraint(model.nodes, rule=_balance)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_obj))
    return {"objective": obj_val, "status": "optimal"}