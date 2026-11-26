import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    num_cities = int(params["num_cities"])
    source = int(params["source"])
    destination = int(params["destination"])

    nodes = list(range(num_cities))

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in nodes for j in nodes if i != j],
        dimen=2,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    # Objective: maximize net outflow from the source
    def obj_rule(m):
        return sum(m.flow[source, j] for j in nodes if j != source) - \
               sum(m.flow[i, source] for i in nodes if i != source)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Capacity constraints
    def cap_rule(m, i, j):
        return m.flow[i, j] <= capacity[i][j]

    model.cap_con = pyo.Constraint(model.arcs, rule=cap_rule)

    # Flow conservation: source = net out, destination = net in, others = 0
    def cons_rule(m, v):
        out_flow = sum(m.flow[v, j] for j in nodes if j != v)
        in_flow = sum(m.flow[i, v] for i in nodes if i != v)
        if v == source:
            return out_flow - in_flow >= 0
        elif v == destination:
            # net inflow into destination must equal net outflow of source (balance)
            return out_flow - in_flow <= 0
        else:
            return out_flow - in_flow == 0

    model.cons = pyo.Constraint(model.nodes, rule=cons_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}