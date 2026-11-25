import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_origins = 4
    num_destinations = 5
    num_products = 2

    origins = range(num_origins)
    destinations = range(num_destinations)
    products = range(num_products)

    model = pyo.ConcreteModel()

    model.origin = pyo.Set(initialize=origins)
    model.destination = pyo.Set(initialize=destinations)
    model.product = pyo.Set(initialize=products)

    model.x = pyo.Var(
        model.origin, model.destination, model.product,
        domain=pyo.NonNegativeReals,
    )

    # Cost lookup: support either flat (origin-major, dest-minor, product-innermost)
    # or nested [origin][destination][product] structures.
    def get_cost(o, d, p):
        if isinstance(cost[o], (list, tuple)):
            return cost[o][d][p]
        return cost[o * num_destinations * num_products
                    + d * num_products + p]

    # Objective: minimize total transportation cost
    model.total_cost = pyo.Objective(
        expr=sum(
            get_cost(o, d, p) * model.x[o, d, p]
            for o in model.origin
            for d in model.destination
            for p in model.product
        ),
        sense=pyo.minimize,
    )

    # Supply constraints: all supply from each origin/product must be fully utilized
    def supply_rule(mdl, o, p):
        return sum(mdl.x[o, d, p] for d in mdl.destination) == supply[o][p]
    model.supply_constraint = pyo.Constraint(
        model.origin, model.product, rule=supply_rule
    )

    # Demand constraints: all demand at each destination/product must be met
    def demand_rule(mdl, d, p):
        return sum(mdl.x[o, d, p] for o in mdl.origin) == demand[d][p]
    model.demand_constraint = pyo.Constraint(
        model.destination, model.product, rule=demand_rule
    )

    # Capacity constraints: combined products per origin-destination pair
    def capacity_rule(mdl, o, d):
        return sum(mdl.x[o, d, p] for p in mdl.product) <= capacity[o][d]
    model.capacity_constraint = pyo.Constraint(
        model.origin, model.destination, rule=capacity_rule
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}