import math
import numpy as np
import matplotlib.pyplot as plt


# CONSTANTS FÍSIQUES I FACTORS DE CONVERSIÓ

G = 9.80665          # Acceleració de la gravetat (m/s^2)
R = 287.058          # Constant específica dels gasos per a l'aire (J/(kg*K))
GAMMA = 1.4
RHO_0 = 1.225        # Densitat a nivell del mar (kg/m^3)
T0 = 288.15          # Temperatura a nivell del mar (K)
L = -0.0065          # Gradient tèrmic vertical ISA a la troposfera (K/m)
FT_TO_M = 0.3048
M_TO_FT = 1.0 / FT_TO_M
KT_TO_MPS = 0.514444
MPS_TO_KT = 1.0 / KT_TO_MPS
TONS_TO_KG = 1000.0


def isa_atmosphere(alt_m: float):
    if alt_m <= 11000.0:  # Troposfera
        T = T0 + L * alt_m
        P = 101325.0 * (T / T0) ** (-G / (L * R))
    else:  # Estratosfera baixa isotèrmica
        T = 216.65
        T_11 = T0 + L * 11000.0
        P_11 = 101325.0 * (T_11 / T0) ** (-G / (L * R))
        P = P_11 * math.exp(-G * (alt_m - 11000.0) / (R * T))

    rho = P / (R * T)
    return T, P, rho




# CLASSE AVIÓ I COEFICIENTS BADA

class Avio:
    def __init__(
            self,
            model: str,
            mlw: float,          # tons
            mtow: float,         # tons
            max_payload: float,  # tons
            s: float,            # m^2
            cd0_app: float,
            cd2_app: float,
            cd0_clean: float,
            cd2_clean: float,
            hp_desc: float,      # ft
            ct_desc_high: float,
            ct_desc_low: float,
            ct_desc_app: float,
            ct1: float,          # N
            ct2: float,          # ft
            ct3: float,          # 1/ft^2
            cf1: float,          # kg/(min*kN)
            cf2: float           # kt
    ):
        self.model = model
        self.mlw = mlw
        self.mtow = mtow
        self.max_payload = max_payload
        self.s = s
        self.cd0_app = cd0_app
        self.cd2_app = cd2_app
        self.cd0_clean = cd0_clean
        self.cd2_clean = cd2_clean
        self.hp_desc = hp_desc
        self.ct_desc_high = ct_desc_high
        self.ct_desc_low = ct_desc_low
        self.ct_desc_app = ct_desc_app
        self.ct1 = ct1
        self.ct2 = ct2
        self.ct3 = ct3
        self.cf1 = cf1
        self.cf2 = cf2


# Models + coeficients BADA

b767 = Avio(
    model="B767-300ER",
    mlw=145.15, mtow=204.10, max_payload=46.50, s=283.50,
    cd0_app=0.01400, cd2_app=0.04900, cd0_clean=0.01740, cd2_clean=0.04590,
    hp_desc=26418.0, ct_desc_high=0.064359, ct_desc_low=0.055988, ct_desc_app=0.12475,
    ct1=0.35167e6, ct2=0.44673e5, ct3=0.10129e-9,
    cf1=0.54005, cf2=557.82
)

b777 = Avio(
    model="B777-300",
    mlw=237.68, mtow=299.30, max_payload=64.90, s=428.04,
    cd0_app=0.01730, cd2_app=0.04840, cd0_clean=0.01570, cd2_clean=0.04200,
    hp_desc=36122.0, ct_desc_high=0.044239, ct_desc_low=0.041065, ct_desc_app=0.092921,
    ct1=0.42577e6, ct2=0.48987e5, ct3=0.66146e-10,
    cf1=0.87843, cf2=3689.7)

b737 = Avio(
    model="B737",
    mlw=51.71, mtow=70.80, max_payload=16.92, s=124.65,
    cd0_app=0.02700, cd2_app=0.04410, cd0_clean=0.02350, cd2_clean=0.04450,
    hp_desc=30152.0, ct_desc_high=0.036336, ct_desc_low=0.053395, ct_desc_app=0.16440,
    ct1=0.14573e6, ct2=0.55638e5, ct3=0.14200e-10,
    cf1=0.94680, cf2=1.0000e14)

a320 = Avio(
    model="A320-212",
    mlw=64.50, mtow=77.00, max_payload=21.50, s=122.60,
    cd0_app=0.02420, cd2_app=0.04690, cd0_clean=0.02400, cd2_clean=0.03750,
    hp_desc=12398.0, ct_desc_high=0.045711, ct_desc_low=0.027207, ct_desc_app=0.13981,
    ct1=0.13605e6, ct2=0.52238e5, ct3=0.26637e-10,
    cf1=0.94000, cf2=1.0000e5)

a319 = Avio(
    model="A319-131",
    mlw=61.00, mtow=70.00, max_payload=17.00, s=122.60,
    cd0_app=0.02840, cd2_app=0.03760, cd0_clean=0.02800, cd2_clean=0.03100,
    hp_desc=27726.0, ct_desc_high=0.083084, ct_desc_low=0.051765, ct_desc_app=0.14767,
    ct1=0.13900e6, ct2=0.58900e5, ct3=0.57200e-14,
    cf1=0.68800, cf2=1670.0)


def get_aircraft(ac_type: str) -> Avio:
    """Retorna l'objecte Avio segons el model concret."""
    nom = ac_type.strip().upper()
    if nom == "B767-300ER":
        return b767
    elif nom == "B777-300":
        return b777
    elif nom == "B737":
        return b737
    elif nom == "A320-212":
        return a320
    elif nom == "A319-131":
        return a319
    else:
        raise ValueError(f"Model d'avió desconegut: {ac_type}")



# AIRCRAFT PERFORMANCE I EQUACIONS DE VOL

def compute_thrust_idle(ac: Avio, hp_ft: float) -> float:
    t_max = ac.ct1 * (1.0 - (hp_ft / ac.ct2) + ac.ct3 * (hp_ft ** 2))
    if hp_ft > ac.hp_desc:  # Configuració sobre 6000 ft
        t_desc = ac.ct_desc_high * t_max
    else:
        if hp_ft <= 6000.0:  # Configuració d'aproximació sota 6000 ft
            t_desc = ac.ct_desc_app * t_max
        else:                # Configuració neta
            t_desc = ac.ct_desc_low * t_max
    return t_desc


def compute_aerodynamics(ac: Avio, weight_kg: float, rho: float, v_m_s: float, hp_ft: float):
    if hp_ft <= 6000.0:
        cd0 = ac.cd0_app
        cd2 = ac.cd2_app
    else:
        cd0 = ac.cd0_clean
        cd2 = ac.cd2_clean

    l_force = weight_kg * G
    cl = (2.0 * l_force) / (rho * (v_m_s ** 2) * ac.s)
    cd = cd0 + cd2 * (cl ** 2)
    drag = 0.5 * rho * (v_m_s ** 2) * ac.s * cd
    return cl, cd, drag


def compute_v_min_rod(ac: Avio, weight_kg: float, rho: float, thrust_n: float, hp_ft: float) -> float:
    if hp_ft <= 6000.0:
        cd0 = ac.cd0_app
        cd2 = ac.cd2_app
    else:
        cd0 = ac.cd0_clean
        cd2 = ac.cd2_clean

    mg = weight_kg * G
    inner_root = math.sqrt(thrust_n ** 2 + 12.0 * cd0 * cd2 * (mg ** 2))
    v_sq = (thrust_n + inner_root) / (3.0 * cd0 * rho * ac.s)
    return math.sqrt(v_sq)


def compute_fuel_flow(ac: Avio, v_m_s: float, thrust_n: float) -> float:
    v_kt = v_m_s * MPS_TO_KT
    eta = ac.cf1 * (1.0 + (v_kt / ac.cf2))
    thrust_kn = thrust_n / 1000.0
    ff_kg_min = eta * thrust_kn
    return ff_kg_min / 60.0



# SIMULADOR CDO BACKWARD

def getCDO(aircraft_model: str, MLW_percent: float):
    ac = get_aircraft(aircraft_model)
    weight_kg = (ac.mlw * TONS_TO_KG) * (MLW_percent / 100.0)

    h_ft = 6000.0
    h_m = h_ft * FT_TO_M
    x_m = 0.0
    t_s = 0.0
    dt = -1.0

    x_traj = [x_m]
    h_traj = [h_m]
    v_traj = []

    while h_ft < 40000.0:
        _, _, rho = isa_atmosphere(h_m)
        thrust_idle = compute_thrust_idle(ac, h_ft)
        v = compute_v_min_rod(ac, weight_kg, rho, thrust_idle, h_ft)
        _, _, drag = compute_aerodynamics(ac, weight_kg, rho, v, h_ft)
        v_traj.append(v)

        rod = v * (drag - thrust_idle) / (weight_kg * G)
        sin_gamma = max(-1.0, min(1.0, rod / v))
        cos_gamma = math.sqrt(max(0.0, 1.0 - sin_gamma ** 2))
        vx = v * cos_gamma

        ff = compute_fuel_flow(ac, v, thrust_idle)

        dh_dt = -rod
        dx_dt = vx
        dm_dt = -ff

        h_m += dh_dt * dt
        h_ft = h_m * M_TO_FT
        x_m += dx_dt * dt
        weight_kg += dm_dt * dt
        t_s += dt

        x_traj.append(x_m)
        h_traj.append(h_m)

    v_traj.append(v_traj[-1])

    return np.array(x_traj), np.array(h_traj), np.array(v_traj)


# ==========================================
# 5. GENERACIÓ DEL GRÀFIC (Diapositiva 2)
# ==========================================
if __name__ == "__main__":
    casos_presentacio = [
        ("B767-300ER", 100.0),
        ("B767-300ER", 80.0),
        ("B777-300", 100.0),
        ("B777-300", 80.0),
        ("B737", 100.0),
        ("B737", 80.0),
        ("A320-212", 100.0),
        ("A320-212", 80.0),
        ("A319-131", 100.0),
        ("A319-131", 80.0),
    ]

    plt.figure(figsize=(10, 6.5))

    print("--- COMPUTANT TRAJECTÒRIES CDO A MÍNIM ROD ---")
    for model, pct in casos_presentacio:
        x, h, _ = getCDO(aircraft_model=model, MLW_percent=pct)
        label = f"{model} [{int(pct)}% MLW]"
        plt.plot(x, h, label=label, linewidth=1.2)
        print(f"Completat: {label} -> ToD a x = {x[-1]:.0f} m, h = {h[-1]:.0f} m")

    plt.xlabel("x [m]", fontsize=10)
    plt.ylabel("h [m]", fontsize=10)
    plt.grid(True, linestyle="-", alpha=0.3)
    plt.legend(loc="upper right", fontsize=7.5)
    plt.tight_layout()
    plt.show()