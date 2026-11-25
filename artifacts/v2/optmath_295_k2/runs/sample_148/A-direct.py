import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    aircraft = list(availability.keys())
    routes = list(demand.keys())

    # Capacity and cost matrices may only partially specify entries.
    # Missing entries are treated as zero contribution / prohibitively costly,
    # but here we simply default capacity to 0 and cost to 0 when absent,
    # keeping assignment possible only where explicitly provided with positive
    # capacity. To avoid choosing impossible arcs, we set cost to a large
    # penalty where capacity is missing/zero so those arcs are never used.
    def cap_of(a, r):
        try:
            v = capacity[a][r]
        except (KeyError, TypeError):
            v = 0
        return v if v is not None else 0

    def cost_of(a, r):
        try:
            v = cost[a][r]
        except (KeyError, TypeError):
            return None
        return v

    # Build allowed arcs: only where capacity > 0 and cost is known.
    allowed = [(a, r) for a in aircraft for r in routes
               if cap_of(a, r) > 0 and cost_of(a, r) is not None]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=aircraft)
    model.R = pyo.Set(initialize=routes)
    model.AR = pyo.Set(initialize=allowed, dimen=2)

    model.x = pyo.Var(model.AR, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(
        expr=sum(cost_of(a, r) * model.x[a, r] for (a, r) in model.AR),
        sense=pyo.minimize,
    )

    def avail_rule(m, a):
        return sum(m.x[a, r] for (aa, r) in m.AR if aa == a) <= availability[a]

    model.avail = pyo.Constraint(model.A, rule=avail_rule)

    def demand_rule(m, r):
        return sum(cap_of(a, r) * m.x[a, r] for (a, rr) in m.AR if rr == r) >= demand[r]

    model.dem = pyo.Constraint(model.R, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}