import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    days = params["days"]
    max_demand = params["max_demand"]
    price = params["price"]
    prod_cost = params["prod_cost"]
    quota = params["quota"]
    activation_cost = params["activation_cost"]
    min_batch = params["min_batch"]

    products = [0, 1, 2]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, domain=pyo.Binary)

    def _obj(m):
        return sum(
            (price[p] - prod_cost[p]) * m.x[p] - activation_cost[p] * m.y[p]
            for p in m.P
        )
    model.profit = pyo.Objective(rule=_obj, sense=pyo.maximize)

    def _demand(m, p):
        return m.x[p] <= max_demand[p]
    model.demand_con = pyo.Constraint(model.P, rule=_demand)

    def _capacity(m, p):
        return m.x[p] <= quota[p] * days * m.y[p]
    model.capacity_con = pyo.Constraint(model.P, rule=_capacity)

    def _minbatch(m, p):
        return m.x[p] >= min_batch[p] * m.y[p]
    model.minbatch_con = pyo.Constraint(model.P, rule=_minbatch)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}