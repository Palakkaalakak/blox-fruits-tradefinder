#!/usr/bin/env python3
"""
Physically-motivated models for the Doom.

None of this is a true geophysical simulation — no finite elements, no mantle
rheology, no shock hydrocode. But several of the Doom's consequences follow
from closed-form physics that CAN be computed honestly, and doing so produces
patterns that are correlated in the way real ones would be, rather than
independently invented.

What is genuinely computed here:

  1. ROTATIONAL BULGE READJUSTMENT after the pole shift. The real mechanism,
     with the real numbers.
  2. IMPACT CRATER from pi-group scaling laws (Schmidt-Housen), rather than a
     Gaussian pit of arbitrary size.
  3. EJECTA BLANKET with the observed r^-3 thickness falloff.
  4. ANTIPODAL DISRUPTION from seismic focusing — a real, observed effect on
     Mercury and the Moon.
  5. FLEXURAL ISOSTASY: the lithosphere responds to loading as an elastic
     plate, which is a smoothing at the flexural wavelength.

What is still faked: the crustal deformation itself (domain warping),
and the fracture network's geometry.
"""

import numpy as np
from scipy import ndimage

# --- Earth constants -------------------------------------------------------
OMEGA = 7.2921e-5          # rad/s, rotation rate
R_EARTH = 6.371e6          # m
G = 9.81                   # m/s^2
RHO_CRUST = 2700.0         # kg/m^3
RHO_MANTLE = 3300.0        # kg/m^3
RHO_TARGET = 2700.0
RHO_IMPACTOR = 3000.0


def _latlon_grids(h, w):
    lat = np.linspace(np.pi / 2, -np.pi / 2, h)[:, None]
    lon = np.linspace(-np.pi, np.pi, w, endpoint=False)[None, :]
    return lat, lon


def _unit_vectors(h, w):
    lat, lon = _latlon_grids(h, w)
    cl = np.cos(lat)
    return np.stack([
        np.broadcast_to(cl * np.cos(lon), (h, w)),
        np.broadcast_to(cl * np.sin(lon), (h, w)),
        np.broadcast_to(np.broadcast_to(np.sin(lat), (h, 1)), (h, w)),
    ])


def rotation_matrix(alpha, beta, gamma):
    a, b, g = np.radians([alpha, beta, gamma])
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(g), -np.sin(g)], [0, np.sin(g), np.cos(g)]])
    return Rz @ Ry @ Rx


# ---------------------------------------------------------------------------
# 1. Rotational bulge readjustment  (the big one)
# ---------------------------------------------------------------------------

def bulge_readjustment(h, w, rotation, response=0.18):
    """Relative sea-level change after true polar wander.

    Earth's 21 km equatorial bulge is a rotational effect: the hydrostatic
    figure follows the centrifugal potential, whose degree-2 part is

        Phi(theta) = -(1/3) * omega^2 * R^2 * P2(cos theta)

    giving an equilibrium sea surface offset of

        N(theta) = (omega^2 R^2 / 3g) * P2(cos theta)      [~7.3 km scale]

    Move the rotation axis and the oceans re-level onto the NEW geoid within
    days, while the solid Earth — which still carries the OLD bulge — relaxes
    over ~10^5 years. In the meantime, relative sea level changes by

        dh(x) = N(theta_new(x)) - N(theta_old(x))

    which is the single most dramatic thing a pole shift does to a map. It
    drowns whole regions and lifts others clear of the sea, and it does so in
    a smooth quadrupole pattern tied directly to the geometry of the shift —
    not at random.

    `response` scales for the fact that the solid Earth partially follows
    (and that a full 7 km swing would be absurd for a habitable world).
    Returns metres of relative sea-level rise; positive means drowning.
    """
    v = _unit_vectors(h, w)                      # positions in the NEW frame
    R = rotation_matrix(*rotation)

    # The same material point in the OLD frame
    v_old = np.tensordot(R.T, v, axes=(1, 0))

    def p2(cos_theta):
        return 0.5 * (3.0 * cos_theta ** 2 - 1.0)

    scale = (OMEGA ** 2 * R_EARTH ** 2) / (3.0 * G)    # ~7332 m
    n_new = scale * p2(v[2])                            # z-component = cos(colat)
    n_old = scale * p2(v_old[2])
    return response * (n_new - n_old)


# ---------------------------------------------------------------------------
# 2-4. Impact
# ---------------------------------------------------------------------------

def crater_diameter(impactor_d_m, velocity_ms=20000.0, angle_deg=45.0,
                    gravity=G):
    """Final crater diameter from pi-group scaling (Schmidt-Housen form).

    Transient crater, gravity regime:
        D_t = 1.161 * (rho_i/rho_t)^(1/3) * L^0.78 * v^0.44 * g^-0.22
              * sin(angle)^(1/3)
    Simple-to-complex collapse then widens it by roughly 1.25x for large
    craters.
    """
    L = impactor_d_m
    v = velocity_ms
    dt = (1.161 * (RHO_IMPACTOR / RHO_TARGET) ** (1.0 / 3.0)
          * L ** 0.78 * v ** 0.44 * gravity ** -0.22
          * np.sin(np.radians(angle_deg)) ** (1.0 / 3.0))
    return 1.25 * dt


def impact_field(h, w, lat_deg, lon_deg, impactor_d_m=14000.0,
                 velocity_ms=20000.0, angle_deg=45.0):
    """Crater cavity, rim uplift, ejecta blanket and antipodal disruption.

    Depth/diameter for large complex craters is ~1/25. Ejecta thickness falls
    off as (r/R)^-3, the observed lunar relation. Antipodal disruption comes
    from seismic waves converging on the far side — chaotic terrain sits
    opposite the Caloris basin on Mercury and opposite Imbrium on the Moon.
    """
    D = crater_diameter(impactor_d_m, velocity_ms, angle_deg)   # metres
    R_crater = D / 2.0
    depth = D / 25.0

    # angular radius on the sphere -> pixels
    ang = R_crater / R_EARTH                       # radians
    r_px = ang / np.pi * h

    v = _unit_vectors(h, w)
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    c = np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])

    cosd = np.clip(np.tensordot(c, v, axes=(0, 0)), -1, 1)
    dist = np.arccos(cosd) / np.pi * h              # great-circle distance, px
    anti = np.arccos(np.clip(-cosd, -1, 1)) / np.pi * h

    out = np.zeros((h, w), dtype=np.float32)

    # cavity: parabolic bowl inside the rim
    inside = dist < r_px
    out[inside] -= depth * (1.0 - (dist[inside] / r_px) ** 2)

    # rim uplift, ~4% of depth, concentrated at the rim
    rim = depth * 0.9 * np.exp(-((dist - r_px) / (0.28 * r_px)) ** 2)
    out += rim

    # ejecta blanket: t = 0.14 * R * (r/R)^-3 beyond the rim
    outside = dist >= r_px
    t = np.zeros_like(out)
    t[outside] = 0.14 * R_crater * (dist[outside] / r_px) ** -3.0
    out += np.clip(t, 0, depth * 1.5)

    # antipodal disruption: seismic focusing on the far side
    focus = np.exp(-(anti / (2.2 * r_px)) ** 2)
    out += 0.10 * depth * focus

    return out.astype(np.float32), D


# ---------------------------------------------------------------------------
# 5. Flexural isostasy
# ---------------------------------------------------------------------------

def flexural_response(load_m, h, w, Te_m=25000.0):
    """Lithospheric flexure under a load.

    The elastic plate equation D*grad^4(z) + (rho_m - rho_i)*g*z = q has a
    Green's function whose width is the flexural parameter

        alpha = (4D / ((rho_m - rho_c) g))^(1/4),    D = E*Te^3 / (12(1-v^2))

    Rather than solving the biharmonic, this approximates the response as a
    Gaussian smoothing at that wavelength scaled by the density ratio — which
    captures the essential behaviour: the lithosphere does not respond
    locally, it spreads a load over hundreds of kilometres.
    """
    E, nu = 1.0e11, 0.25
    D = E * Te_m ** 3 / (12.0 * (1 - nu ** 2))
    alpha = (4.0 * D / ((RHO_MANTLE - RHO_CRUST) * G)) ** 0.25    # metres
    sigma_px = (alpha / (np.pi * R_EARTH)) * h                    # -> pixels
    sigma_px = float(np.clip(sigma_px, 1.0, h / 6.0))

    smoothed = ndimage.gaussian_filter(load_m, sigma_px,
                                       mode=("nearest", "wrap"))
    return -(RHO_CRUST / RHO_MANTLE) * smoothed, alpha, sigma_px
