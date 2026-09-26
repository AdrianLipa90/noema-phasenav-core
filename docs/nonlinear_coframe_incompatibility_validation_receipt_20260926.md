# Nonlinear Coframe Incompatibility Firewall Validation Receipt
Date: 2026-09-26
Status: PASS / RAW_CURL_CURVATURE_NO_GO

Branch:

    formalism/nonlinear-coframe-incompatibility-firewall-v0.1-20260926

Independent controls:

1. Local rotating flat triad:
       E=R_z(theta)
   gives
       E^T E=I
   with numeric metric residual 3.01e-17 on the control.

2. For theta=b x with b=0.7:
       ||Curl E||=0.7
   while the metric is exactly flat.

3. Torsion-free spin connection
       omega=-J_z dtheta
   has
       Omega=domega+omega wedge omega=0
   for commuting mixed partials.

4. Nonflat conformal triad:
       E=diag(e^sigma,e^sigma,1),
       sigma=a(x^2+y^2)
   has
       Curl E=0
   at the origin while
       R=-8a
   there; for a=0.2, R=-1.6.

Verdict:

    RAW_COFRAME_CURL != INTRINSIC_CURVATURE.

Raw Curl is neither sufficient nor pointwise necessary for curvature.
Material incompatibility and Cartan torsion remain separate typed concepts.
