import math

def haversine_distance(coord1: tuple[float, float], coord2: tuple[float, float]):
    lon1, lat1 = coord1
    lon2, lat2 = coord2

    # Promień Ziemi w kilometrach
    R = 6371.0

    # Konwersja stopni na radiany
    # Używamy LaTeX do wzoru: $$rad = deg \times \frac{\pi}{180}$$
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Wzór Haversine
    # $$a = \sin^2(\frac{\Delta\phi}{2}) + \cos(\phi_1) \cdot \cos(\phi_2) \cdot \sin^2(\frac{\Delta\lambda}{2})$$
    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2)**2

    # $$c = 2 \cdot \operatorname{atan2}(\sqrt{a}, \sqrt{1-a})$$
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Odległość $$d = R \cdot c$$
    distance = R * c

    return distance