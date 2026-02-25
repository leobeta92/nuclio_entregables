
def unit_price(quantity, price):
    return price / quantity

def calc_ingresos(quantity, price):
    return quantity * price

def total_share(value, df):
    return value / df.shape[0]

def dia_de_la_semana(value):
    dias_de_la_semana = {
        0: 'Lunes',
        1: 'Martes',
        2: 'Miercoles',
        3: 'Jueves',
        4: 'Viernes',
        5: 'Sabado',
        6: 'Domingo'
    }

    return dias_de_la_semana[value.day_of_week]