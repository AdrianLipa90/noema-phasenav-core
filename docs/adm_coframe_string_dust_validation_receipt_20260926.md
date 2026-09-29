# ADM Coframe + String-Dust Source Reference Validation Receipt
Date: 2026-09-26
Status: PASS / TYPED_COFRAME_AND_SOURCE_REFERENCE

Branch:

    formalism/adm-coframe-source-reference-v0.1-20260926

Independent checks:

ADM/coframe:
- direct g=e^T eta e agrees with the ADM formula to Frobenius residual
  9.81e-18 on the numeric control;
- recovery of lapse, shift and triad from the declared time-gauge coframe has
  aggregate numeric residual 6.94e-18;
- N=1, beta=0 recovers the prior spatial GL(3) Bivector36 carrier;
- the quadratic-conformal Cartan reference is exactly the ADM special case
  E=diag(e^sigma,e^sigma,1), N=1, beta=0.

Independent source:
- aligned string-dust tensor
      T_cov=diag(rho,0,0,-rho)
  is defined independently of G;
- symbolic covariant divergence on the reference metric is exactly zero for
  arbitrary static transverse rho(x,y);
- exact Einstein match with Lambda=0 requires
      rho=-(4a/kappa)e^(-2sigma);
- for kappa>0, positive rho requires a<0;
- matched proper energy per coordinate transverse area is exactly
      rho e^(2sigma)=-4a/kappa,
  hence constant;
- therefore total matched source energy on an infinite transverse plane grows
  without bound with area.

Verdict:

    ADM_TRIAD_TO_COFRAME = PASS_AS_TYPED_KINEMATICS
    STRING_DUST_MATCH = PASS_AS_INDEPENDENT_REFERENCE_SOURCE

This is not evidence that the physical PhaseNav/Moire state is spacetime or
that string dust is the realized source.
