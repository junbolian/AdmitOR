def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    # Prices (Klunz per unit)
    p_steel = params["steel_price"]
    p_eng = params["engines_price"]
    p_elec = params["electronics_price"]
    p_plas = params["plastics_price"]

    # Inter-industry requirements
    a_steel_eng = params["a_steel_engines"]
    a_steel_plas = params["a_steel_plastics"]
    a_eng_steel = params["a_engines_steel"]
    a_eng_elec = params["a_engines_electronics"]
    a_eng_plas = params["a_engines_plastics"]
    a_elec_steel = params["a_electronics_steel"]
    a_elec_eng = params["a_electronics_engines"]
    a_elec_plas = params["a_electronics_plastics"]
    a_plas_eng = params["a_plastics_engines"]
    a_plas_steel = params["a_plastics_steel"]
    a_plas_elec = params["a_plastics_electronics"]

    # Import costs (Klunz per unit)
    ic_steel = params["import_cost_steel"]
    ic_eng = params["import_cost_engines"]
    ic_elec = params["import_cost_electronics"]
    ic_plas = params["import_cost_plastics"]

    # Labor requirements
    lab_steel = params["labor_steel"]          # person-months
    lab_eng = params["labor_engines"]          # person-years
    lab_elec = params["labor_electronics"]     # person-months
    lab_plas = params["labor_plastics"]        # person-years

    # Capacities
    eng_cap = params["engine_capacity"]
    plas_cap = params["plastics_capacity"]
    labor_cap = params["labor_capacity"]

    # Convert person-months to person-years (12 months per year)
    months_per_year = 12

    model = pyo.ConcreteModel()

    # Decision variables: gross production of each commodity
    model.x_steel = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_engines = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_electronics = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_plastics = pyo.Var(domain=pyo.NonNegativeReals)

    # Net exports (production minus intermediate use minus imports)
    # GDP in market prices = value of net exports for each good
    def obj_rule(m):
        net_steel = m.x_steel - a_eng_steel * m.x_engines - a_elec_steel * m.x_electronics - a_plas_steel * m.x_plastics
        net_eng = m.x_engines - a_steel_eng * m.x_steel - a_elec_eng * m.x_electronics - a_plas_eng * m.x_plastics
        net_elec = m.x_electronics - a_eng_elec * m.x_engines - a_plas_elec * m.x_plastics
        net_plas = m.x_plastics - a_steel_plas * m.x_steel - a_eng_plas * m.x_engines - a_elec_plas * m.x_electronics
        imports = (ic_steel * m.x_steel + ic_eng * m.x_engines +
                   ic_elec * m.x_electronics + ic_plas * m.x_plastics)
        return (p_steel * net_steel + p_eng * net_eng +
                p_elec * net_elec + p_plas * net_plas - imports)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Capacity constraints
    model.eng_cap_con = pyo.Constraint(expr=model.x_engines <= eng_cap)
    model.plas_cap_con = pyo.Constraint(expr=model.x_plastics <= plas_cap)

    # Labor constraint (convert person-months to person-years)
    def labor_rule(m):
        return ((lab_steel / months_per_year) * m.x_steel +
                lab_eng * m.x_engines +
                (lab_elec / months_per_year) * m.x_electronics +
                lab_plas * m.x_plastics) <= labor_cap

    model.labor_con = pyo.Constraint(rule=labor_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "solve_failed: " + type(exc).__name__}