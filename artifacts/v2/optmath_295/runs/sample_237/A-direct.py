import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    companies = range(5)
    markets = range(4)
    products = range(2)

    profit = {}
    for co in companies:
        for ma in markets:
            for pr in products:
                profit[(co, ma, pr)] = params[f"profit_co{co}_ma{ma}_pr{pr}"]

    demand = {}
    for ma in markets:
        for pr in products:
            demand[(ma, pr)] = params[f"demand_ma{ma}_pr{pr}"]

    model = pyo.ConcreteModel()

    model.COMP = pyo.Set(initialize=list(companies))
    model.MARK = pyo.Set(initialize=list(markets))
    model.PROD = pyo.Set(initialize=list(products))

    model.x = pyo.Var(model.COMP, model.MARK, model.PROD, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[(co, ma, pr)] * m.x[co, ma, pr]
                   for co in m.COMP for ma in m.MARK for pr in m.PROD)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, ma, pr):
        return sum(m.x[co, ma, pr] for co in m.COMP) == demand[(ma, pr)]

    model.demand_con = pyo.Constraint(model.MARK, model.PROD, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}