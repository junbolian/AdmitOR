import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]
    pair_capacity = params["pair_capacity"]

    n = len(supply)
    m = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=range(n))
    model.destinations = pyo.Set(initialize=range(m))
    model.arcs = pyo.Set(initialize=[(i, j) for i in range(n) for j in range(m)])

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def transport_cost_rule(mdl, i, j):
        return transport_cost[i][j] * mdl.flow[i, j]

    model.transport_cost_expr = pyo.Expression(
        model.arcs, rule=transport_cost_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.transport_cost_expr[i, j] for (i, j) in model.arcs),
        sense=pyo.minimize,
    )

    def supply_capacity_rule(mdl, i):
        return sum(mdl.flow[i, j] for j in range(m)) <= supply[i]

    model.supply_capacity = pyo.Constraint(model.origins, rule=supply_capacity_rule)

    def supply_utilization_rule(mdl, i):
        return sum(mdl.flow[i, j] for j in range(m)) >= supply[i]

    model.supply_utilization = pyo.Constraint(
        model.origins, rule=supply_utilization_rule
    )

    def demand_satisfaction_rule(mdl, j):
        return sum(mdl.flow[i, j] for i in range(n)) == demand[j]

    model.demand_satisfaction = pyo.Constraint(
        model.destinations, rule=demand_satisfaction_rule
    )

    def pair_capacity_rule(mdl, i, j):
        return mdl.flow[i, j] <= pair_capacity[i][j]

    model.pair_capacity = pyo.Constraint(model.arcs, rule=pair_capacity_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}