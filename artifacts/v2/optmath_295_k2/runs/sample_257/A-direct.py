import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Nodes and directed arcs (all ordered pairs i != j)
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def cost(i, j):
        return params["c_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    # Binary route-usage decisions
    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    # Objective: minimize total cost of used routes
    def _obj(m):
        return sum(cost(i, j) * m.x[(i, j)] for (i, j) in arcs)

    model.obj_expr = pyo.Expression(rule=_obj)
    model.OBJ = pyo.Objective(expr=model.obj_expr, sense=pyo.minimize)

    supply0 = params["supply_node0"]
    demand7 = params["demand_node7"]

    # Flow balance: net outflow at node n = sum_out - sum_in
    def _balance_rule(m, n):
        outflow = sum(m.x[(n, j)] for j in nodes if j != n)
        inflow = sum(m.x[(i, n)] for i in nodes if i != n)
        if n == 0:
            return outflow - inflow == supply0
        elif n == 7:
            return inflow - outflow == demand7
        else:
            return outflow - inflow == 0

    model.BAL = pyo.Constraint(nodes, rule=_balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.OBJ))
    return {"objective": obj_val, "status": "optimal"}